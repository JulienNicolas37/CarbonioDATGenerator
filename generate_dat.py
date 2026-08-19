#!/usr/bin/env python3
"""
generate_dat.py --- Génère un Document d'Architecture Technique (DAT) LaTeX
pour une plateforme Zextras Carbonio, à partir d'un fichier de configuration
client (YAML) et d'un ensemble de templates modulaires (Jinja2 + .tex).

Usage:
    python3 generate_dat.py config/client_exemple.yaml
    python3 generate_dat.py config/client_exemple.yaml --outdir build --compile

Modularité:
    - Chaque composant Carbonio (proxy, mta, mailbox, directory, database,
      files, monitoring, ...) est décrit par une entrée dans
      templates/components_catalog.yaml et, optionnellement, un template
      dédié dans templates/partials/components/<id>.tex.j2. S'il n'existe
      pas de template dédié, templates/partials/components/_generic.tex.j2
      est utilisé automatiquement.
    - Le fichier de configuration client (config/customers/*.yaml) ne contient AUCUNE
      logique de mise en forme : uniquement des données (services activés,
      nœuds, IP/hostnames, flux, SLA...).
    - Le schéma réseau (TikZ) est entièrement généré par tikz_builder.py à
      partir des zones/nœuds/flux du fichier de configuration : aucune
      coordonnée n'est à maintenir à la main.
"""
import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from tikz_builder import build_tikz, escape_latex

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
PARTIALS_DIR = TEMPLATES_DIR / "partials"
COMPONENTS_DIR = PARTIALS_DIR / "components"

# Ordre d'assemblage des sections statiques du document.
STATIC_PARTIALS = [
    "cover.tex.j2",
    "revisions.tex.j2",
    "__TOC__",  # marqueur spécial : insère \tableofcontents
    "intro.tex.j2",
    "stakeholders.tex.j2",
    "product.tex.j2",
    "functional_arch.tex.j2",
    "infra_overview.tex.j2",       # ouvre le chapitre "Architecture technique détaillée"
    "topology.tex.j2",
    "node_backup.tex.j2",          # système de sauvegarde des nœuds
    "flow_categories_ref.tex.j2",  # légende des catégories, juste avant les schémas
    "technical_arch_header.tex.j2",
    "__COMPONENTS__",  # marqueur spécial : boucle sur les composants activés
    "ha_backup_security.tex.j2",
    "scheduled_operations.tex.j2", # opérations planifiées, en fin de chapitre 4
    "dns.tex.j2",
    "authentication.tex.j2",
    "__AUTOPROVISIONING__",  # marqueur spécial : inclus seulement si activé
    "__INTERFACES__",  # marqueur spécial : inclus seulement si non vide
    "exploitation.tex.j2",
    "nfr.tex.j2",
    "__MONITORING__",  # marqueur spécial : inclus seulement si services.monitoring
    "support.tex.j2",
    "pra_pca.tex.j2",
    "network_matrix.tex.j2",  # matrice exhaustive des flux --- en fin de document
    "annexes.tex.j2",
]

# NOTE : "sizing.tex.j2" (Dimensionnement) est volontairement absent de cette
# liste --- retiré temporairement du PDF sur demande, les données de sizing
# restent disponibles dans les fichiers de configuration pour réactivation
# ultérieure (il suffit de le réinsérer dans cette liste).


def make_env():
    return Environment(
        loader=FileSystemLoader([str(TEMPLATES_DIR), str(PARTIALS_DIR), str(COMPONENTS_DIR)]),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        lstrip_blocks=True,
    )


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _safe_color_name(category_id):
    import re as _re
    return "flowcat_" + _re.sub(r"[^A-Za-z0-9]", "_", str(category_id))


AUTH_METHOD_LABELS = {
    "native": "Authentification native (login/mot de passe Carbonio)",
    "external_ldap": "Authentification externe LDAP/AD",
    "saml2": "Authentification SAML2 (SSO)",
    "preauth": "Authentification par preauth",
}


def _oui_non(value, default="[à préciser]"):
    if value is None:
        return default
    return "Oui" if value else "Non"


ASSETS_DIR = TEMPLATES_DIR / "assets"
DEFAULT_INTEGRATOR_LOGO = ASSETS_DIR / "logo_zextras_services.png"


def _prepare_logo(source_path, outdir: Path, dest_stem: str):
    """Copie une image de logo dans le répertoire de sortie sous un nom de
    fichier simple (sans espace/accent), pour un \\includegraphics fiable
    quel que soit le nom/emplacement d'origine. Retourne le nom de fichier
    relatif à utiliser dans le document, ou None si la source est absente."""
    if not source_path or not Path(source_path).is_file():
        return None
    src = Path(source_path)
    dest_name = f"{dest_stem}{src.suffix.lower()}"
    shutil.copyfile(src, outdir / dest_name)
    return dest_name


def _build_stakeholder_ctx(raw, esc, outdir, config_dir, logo_key, default_logo=None):
    """Construit le contexte d'une partie prenante (client OU intégrateur) :
    identité, description, site web, adresse, contacts, logo."""
    logo_rel = raw.get("logo")
    logo_source = (config_dir / logo_rel) if logo_rel else default_logo
    logo_file = _prepare_logo(logo_source, outdir, logo_key)

    contacts = []
    for c in raw.get("contacts", []) or []:
        if not isinstance(c, dict):
            # Entrée mal formée (simple chaîne au lieu d'un dictionnaire
            # {name, role, email, phone}) : on la garde visible plutôt que
            # de planter, en la plaçant dans le champ "name".
            contacts.append({"name": esc(str(c)), "role": "", "email": "", "email_display": "", "phone": ""})
            continue
        email_raw = c.get("email", "")
        contacts.append({
            "name": esc(c.get("name", "")),
            "role": esc(c.get("role", "")),
            "email": email_raw,  # non échappé : utilisé comme cible de \href
            "email_display": esc(email_raw).replace("@", "@\\allowbreak{}") if email_raw else "",
            "phone": esc(c.get("phone", "")),
        })

    return {
        "name": esc(raw.get("name", "")),
        "long_name": esc(raw.get("long_name", raw.get("name", ""))),
        "description": esc(raw.get("description", "")),
        "website": raw.get("website", ""),  # non échappé : utilisé dans \url
        "address": [esc(line) for line in raw.get("address", []) or []],
        # Version prête à l'emploi pour le template : une ligne de config
        # = une ligne affichée dans le PDF (saut de ligne LaTeX "\\"),
        # plutôt qu'une seule ligne avec des virgules.
        "address_display": "\\\\\n".join(esc(line) for line in raw.get("address", []) or []),
        "emergency_phone": esc(raw.get("emergency_phone", "")),
        "contacts": contacts,
        "logo_file": logo_file,
    }


def derive_flows(nodes_raw, network_equipment_raw, flow_relations_catalog):
    """Dérive la liste des flux réseau ("vérité de terrain") à partir des
    nœuds/composants réellement déclarés dans la config client et du
    catalogue de relations standard (templates/flow_relations.yaml).

    Un blocage technique déclaré sur un nœud (nodes_raw[i].blocked_protocols,
    liste d'ids de catégorie) retire le flux correspondant définitivement
    (schémas ET matrice) --- il ne se produit pas réellement, ce n'est pas
    une simple exclusion visuelle."""
    nodes_by_component = {}
    for n in nodes_raw:
        for c in (n.get("components") or []):
            nodes_by_component.setdefault(c, []).append(n["id"])

    last_equipment_id = network_equipment_raw[-1]["id"] if network_equipment_raw else None

    def resolve_role(role):
        if role == "network_equipment_last":
            return [last_equipment_id] if last_equipment_id else []
        return nodes_by_component.get(role, [])

    blocked_by_node = {n["id"]: set(n.get("blocked_protocols") or []) for n in nodes_raw}

    def is_blocked(node_id, category):
        return category in blocked_by_node.get(node_id, set())

    flows = []
    seen = {}
    for rule in flow_relations_catalog.get("relations", []):
        category = rule["category"]
        for src in resolve_role(rule["from"]):
            for dst in resolve_role(rule["to"]):
                if src == dst:
                    continue
                if is_blocked(src, category) or is_blocked(dst, category):
                    continue
                ports_sig = tuple(sorted((p.get("proto", "TCP"), str(p.get("port", ""))) for p in rule.get("ports", [])))
                key = (src, dst, category, ports_sig)
                if key in seen:
                    # Même flux physique (mêmes ports) déjà généré par une
                    # autre règle --- cas typique de rôles colocalisés sur
                    # le même nœud (ex. Chat + Tasks sur la même application).
                    # On fusionne les libellés/protocoles plutôt que de
                    # dupliquer la ligne dans la matrice.
                    existing = seen[key]
                    label = rule.get("label", "")
                    protocol = rule.get("protocol", "")
                    if label and label not in existing["label"]:
                        existing["label"] = f"{existing['label']} / {label}" if existing["label"] else label
                    if protocol and protocol not in existing["protocol"]:
                        existing["protocol"] = f"{existing['protocol']} / {protocol}" if existing["protocol"] else protocol
                    continue
                entry = {
                    "from": src,
                    "to": dst,
                    "category": category,
                    "label": rule.get("label", ""),
                    "protocol": rule.get("protocol", ""),
                    "ports": rule.get("ports", []),
                }
                seen[key] = entry
                flows.append(entry)

    # --- Mesh : maillage complet (sans notion de sens) entre tous les
    #     nœuds hébergeant le composant "mesh", hors nœuds qui le bloquent
    #     explicitement. ---
    mesh_nodes = [nid for nid in nodes_by_component.get("mesh", []) if not is_blocked(nid, "mesh")]
    for i, n1 in enumerate(mesh_nodes):
        for n2 in mesh_nodes[i + 1:]:
            flows.append({
                "from": n1,
                "to": n2,
                "category": "mesh",
                "label": "Interne (service discovery)",
                "protocol": "Service discovery / coordination",
                "ports": [],
            })

    return flows


def build_context(config, config_filename, outdir=None, config_dir=None):
    def esc(v):
        return escape_latex(v) if isinstance(v, str) else v

    def esc_dict(d):
        return {k: esc(v) for k, v in d.items()}

    def esc_list_of_dicts(items, fallback_key):
        """Comme esc_dict, mais appliqué à une liste --- tolère une entrée
        qui ne serait pas un dictionnaire (erreur de frappe/format dans la
        config client) en la replaçant sous fallback_key plutôt que de
        planter avec une AttributeError peu explicite."""
        result = []
        for it in items or []:
            if isinstance(it, dict):
                result.append(esc_dict(it))
            else:
                result.append({fallback_key: esc(str(it))})
        return result

    outdir = outdir or (BASE_DIR / "build/customers/")
    outdir.mkdir(parents=True, exist_ok=True)
    config_dir = config_dir or Path(".")

    client = esc_dict(config["client"])
    # "confidentiality" (public/client/restreint/confidentiel) alimente la
    # case cochée dans la table de confidentialité (voir intro.tex.j2) ---
    # dérivé de "classification" (texte libre, affiché tel quel sur la
    # couverture) par normalisation simple ; repli sur "confidentiel" (le
    # plus prudent) si la valeur ne correspond à aucune des 4 options.
    _CONF_KEYS = {"public", "client", "restreint", "confidentiel"}
    _classification_norm = str(config["client"].get("classification", "")).strip().lower()
    client["confidentiality"] = _classification_norm if _classification_norm in _CONF_KEYS else "confidentiel"

    # --- Édition Carbonio (Community Edition vs Advanced) --- vit dans
    #     product: (pas client:), au même endroit que product.version, qui
    #     reste l'unique source du numéro de version (pas de second champ
    #     de version dédié à la CE).
    carbonio_edition = str(config.get("product", {}).get("edition", "advanced")).strip().lower()
    if carbonio_edition == "ce":
        carbonio_edition_label = "Community Edition (CE)"
    else:
        carbonio_edition = "advanced"
        carbonio_edition_label = "Carbonio (Advanced)"
    sla = esc_dict(config.get("sla", {}))
    services = config.get("services", {})
    zones = config.get("zones", [])
    raw_nodes = [n for n in (config.get("nodes", []) or []) if isinstance(n, dict)]
    raw_network_equipment = config.get("network_equipment", [])

    catalog = load_yaml(TEMPLATES_DIR / "components_catalog.yaml")
    scope_catalog = load_yaml(TEMPLATES_DIR / "scope_catalog.yaml")
    flow_categories = load_yaml(TEMPLATES_DIR / "flow_categories.yaml")
    component_groups = load_yaml(TEMPLATES_DIR / "component_groups.yaml")
    user_services_catalog = load_yaml(TEMPLATES_DIR / "user_services_catalog.yaml")
    flow_relations_catalog = load_yaml(TEMPLATES_DIR / "flow_relations.yaml")
    # Un client peut surcharger/étendre le catalogue de catégories de flux
    # via la clé optionnelle "flow_categories:" de son propre fichier.
    for cat_id, cat_meta in (config.get("flow_categories") or {}).items():
        flow_categories[cat_id] = {**flow_categories.get(cat_id, {}), **cat_meta}

    zones_by_id = {z["id"]: z for z in zones}

    # --- Pools de répartition de charge --- un identifiant qui désigne
    #     plusieurs nœuds à la fois (ex. plusieurs MTA OUT en HA), pour
    #     éviter d'avoir à les lister un par un dans email_flow_paths,
    #     antispam_antivirus.deployment ou dns.domains[].dkim_carrier.
    #     Volontairement permissif (pas de blocage si un id est erroné) ---
    #     voir _resolve_node_or_pool() ci-dessous et les avertissements
    #     affichés en rouge dans les sections concernées.
    load_balancer_pools_raw = config.get("load_balancer_pools", {}) or {}
    node_ids_set = {n["id"] for n in raw_nodes if isinstance(n, dict) and n.get("id")}

    def _resolve_node_or_pool(token):
        """Résout un token vers la liste des ids de nœuds réels qu'il
        désigne. Retourne (liste_ids, existe) --- existe=False si le
        token ne correspond à aucun nœud ni pool déclaré (faute de
        frappe probable) : rien n'est bloqué, mais l'appelant doit
        afficher un avertissement."""
        if not token:
            return [], False
        if token in load_balancer_pools_raw:
            pool_members = load_balancer_pools_raw.get(token) or []
            return [m for m in pool_members if m in node_ids_set], True
        if token in node_ids_set:
            return [token], True
        return [], False

    # --- Anti-spam / anti-virus : résolu ICI (avant les schémas) car son
    #     déploiement peut nécessiter l'ajout d'une boîte symbolique dans
    #     les nœuds avant que les diagrammes ne soient construits plus bas. ---
    asav_raw = config.get("antispam_antivirus", {}) or {}
    asav_outbound_filtering_bool = bool(asav_raw.get("outbound_filtering"))
    asav_deployment_token = str(asav_raw.get("deployment", "external")).strip()
    asav_deployment_nodes, asav_deployment_exists = (
        ([], True) if asav_deployment_token in ("", "external")
        else _resolve_node_or_pool(asav_deployment_token)
    )
    asav_deployment_warning = None
    if asav_deployment_token not in ("", "external") and not asav_deployment_exists:
        asav_deployment_warning = (
            f"le déploiement déclaré pour l'AS/AV (« {esc(asav_deployment_token)} ») ne correspond "
            f"à aucun nœud ni pool déclaré --- vérifier load_balancer_pools et les identifiants de nœuds."
        )
    antispam_antivirus_ctx = {
        "name": esc(asav_raw.get("name", "[à préciser]")),
        "outbound_filtering": _oui_non(asav_raw.get("outbound_filtering")),
        "inbound_filtering": _oui_non(asav_raw.get("inbound_filtering")),
        "quarantine": _oui_non(asav_raw.get("quarantine")),
        # Rempli plus bas, une fois les domaines DNS traités --- un domaine
        # désigne lui-même son porteur DKIM (dns.domains[].dkim_carrier),
        # il n'y a plus de liste séparée à maintenir ici.
        "dkim_domains_display": "Aucun --- Carbonio gère le DKIM pour tous les domaines",
        "deployment_token": esc(asav_deployment_token) if asav_deployment_token not in ("", "external") else "",
        "deployment_warning": asav_deployment_warning,
    }

    # --- Chemins de flux e-mail personnalisés (relais tiers, AS/AV
    #     intercalé...) --- notation "protocole:sens:maillon1:maillon2:...".
    #     Seul le SMTP est pris en charge pour l'instant (les autres
    #     protocoles restent sur le chemin standard direct). Remplace le
    #     lien standard direct MTA<->pare-feu pour les nœuds concernés,
    #     ne s'ajoute pas à côté. Rien n'est bloqué en cas d'erreur : un
    #     avertissement est simplement affiché dans le chapitre des flux.
    ASAV_EXTERNAL_ID = "__antispam_antivirus_external__"
    email_flow_paths_raw = config.get("email_flow_paths", []) or []
    email_flow_path_warnings = []
    email_flow_removals = set()  # {("from", node_id)} sortant | {("to", node_id)} entrant
    email_flow_extra_flows = []
    needs_asav_external_box = False

    def _resolve_flow_hop(token):
        if token == "antispam_antivirus":
            if asav_deployment_token in ("", "external"):
                return [ASAV_EXTERNAL_ID], None
            if not asav_deployment_exists:
                return [], (
                    f"« antispam_antivirus » référencé dans email_flow_paths, mais son déploiement "
                    f"(« {esc(asav_deployment_token)} ») ne correspond à aucun nœud ni pool déclaré."
                )
            return list(asav_deployment_nodes), None
        members, exists = _resolve_node_or_pool(token)
        if not exists:
            return [], f"« {esc(token)} » référencé dans email_flow_paths ne correspond à aucun nœud ni pool déclaré."
        return members, None

    for _path_str in email_flow_paths_raw:
        if not isinstance(_path_str, str):
            continue
        _tokens = [t.strip() for t in _path_str.split(":")]
        if len(_tokens) < 3:
            email_flow_path_warnings.append(
                f"chemin de flux e-mail mal formé (« {esc(_path_str)} ») --- format attendu : "
                f"protocole:sens:maillon1:maillon2:..."
            )
            continue
        _protocol, _direction, _chain_tokens = _tokens[0], _tokens[1], _tokens[2:]
        if _protocol != "smtp":
            email_flow_path_warnings.append(
                f"le chemin de flux e-mail « {esc(_path_str)} » utilise un protocole non pris en charge "
                f"(« {esc(_protocol)} ») --- seul « smtp » est actuellement supporté."
            )
            continue
        if _direction not in ("outbound", "inbound"):
            email_flow_path_warnings.append(
                f"le chemin de flux e-mail « {esc(_path_str)} » a un sens inconnu (« {esc(_direction)} ») "
                f"--- attendu « outbound » ou « inbound »."
            )
            continue

        _resolved_chain = []
        _path_ok = True
        for _tok in _chain_tokens:
            _ids, _warn = _resolve_flow_hop(_tok)
            if _warn:
                email_flow_path_warnings.append(_warn)
                _path_ok = False
            if ASAV_EXTERNAL_ID in _ids:
                needs_asav_external_box = True
            _resolved_chain.append(_ids)
        if not _path_ok or not _resolved_chain:
            continue

        _first_group, _last_group = _resolved_chain[0], _resolved_chain[-1]
        if _direction == "outbound":
            for _nid in _first_group:
                email_flow_removals.add(("from", _nid))
        else:
            for _nid in _last_group:
                email_flow_removals.add(("to", _nid))

        _last_equipment_id = raw_network_equipment[-1]["id"] if raw_network_equipment else None
        if _last_equipment_id:
            if _direction == "outbound":
                _resolved_chain = _resolved_chain + [[_last_equipment_id]]
            else:
                _resolved_chain = [[_last_equipment_id]] + _resolved_chain

        for _i in range(len(_resolved_chain) - 1):
            for _a in _resolved_chain[_i]:
                for _b in _resolved_chain[_i + 1]:
                    if _a == _b:
                        continue
                    email_flow_extra_flows.append({
                        "from": _a, "to": _b, "category": "smtp",
                        "label": "SMTP", "protocol": "SMTP (chemin personnalisé)",
                        "ports": [{"proto": "TCP", "port": 25}],
                    })

    if needs_asav_external_box:
        _asav_zone_id = next((z["id"] for z in zones if z.get("external")), None)
        if _asav_zone_id is None:
            _asav_zone_id = "__ext_services__"
            zones = zones + [{"id": _asav_zone_id, "label": "Services externes", "external": True}]
            zones_by_id[_asav_zone_id] = {"id": _asav_zone_id, "label": "Services externes", "external": True}
        _asav_name_for_label = asav_raw.get("name", "").strip()
        _asav_label = r"\textbf{AS/AV externe}" + (r"\\{\scriptsize " + escape_latex(_asav_name_for_label) + "}" if _asav_name_for_label else "")
        raw_nodes = raw_nodes + [{
            "id": ASAV_EXTERNAL_ID,
            "zone": _asav_zone_id,
            "label": _asav_label,
            "hostname": _asav_name_for_label,
            "ip": "",
            "components": [],
        }]
        node_ids_set.add(ASAV_EXTERNAL_ID)

    # --- Enrichissement des nœuds (copie de travail pour le schéma TikZ,
    #     qui a besoin des données BRUTES car il fait sa propre gestion de
    #     l'échappement LaTeX en interne) ---
    nodes_raw = []
    for n in raw_nodes:
        n = dict(n)
        zone = zones_by_id.get(n["zone"], {})
        n["external"] = bool(zone.get("external"))
        comps = n.get("components", []) or []
        comp_names = [catalog[c]["name"] for c in comps if c in catalog]
        n["components_display"] = ", ".join(comp_names) if comp_names else ""
        # Variante sans "Mesh" pour l'affichage dans le schéma : Mesh est
        # présent sur ~tous les nœuds d'infrastructure, le préciser dans
        # chaque boîte du schéma n'apporte rien (déjà visible dans le
        # tableau des composants) et alourdit l'affichage.
        comp_names_diagram = [catalog[c]["name"] for c in comps if c in catalog and c != "mesh"]
        n["components_display_diagram"] = ", ".join(comp_names_diagram) if comp_names_diagram else ""
        n.setdefault("hostname", "")
        n.setdefault("ip", "")
        nodes_raw.append(n)

    nodes_by_id = {n["id"]: n for n in nodes_raw}
    equipment_by_id = {eq["id"]: eq for eq in raw_network_equipment}

    def label_for(node_id):
        n = nodes_by_id.get(node_id)
        if n:
            if n.get("label"):
                # Le label est du LaTeX brut fourni tel quel (voir
                # _node_content dans tikz_builder.py) --- ne jamais le
                # rééchapper, sous peine d'afficher "\textbf{...}" en
                # texte littéral dans la matrice de flux.
                return n["label"].split(r"\\")[0]
            return escape_latex(n.get("hostname") or n["id"])
        eq = equipment_by_id.get(node_id)
        if eq:
            return escape_latex(eq.get("label") or eq["id"])
        return escape_latex(node_id)

    # --- Équipements réseau (Internet / routeur / pare-feu...), positionnés
    #     en chaîne au-dessus de toutes les zones. Données brutes pour le
    #     schéma TikZ (échappement interne à tikz_builder). ---
    network_equipment_raw = [dict(eq) for eq in raw_network_equipment]

    # --- Dérivation dynamique des flux réseau ("vérité de terrain") à
    #     partir des nœuds/composants réellement déclarés et du catalogue
    #     de relations standard (templates/flow_relations.yaml), plutôt que
    #     de les lister manuellement dans la config client. Un blocage
    #     technique déclaré sur un nœud (nodes[].blocked_protocols) retire
    #     le flux correspondant PARTOUT (schémas ET matrice), puisqu'il ne
    #     se produit pas réellement. ---
    raw_flows = derive_flows(nodes_raw, network_equipment_raw, flow_relations_catalog)

    # --- Applique les chemins de flux e-mail personnalisés (voir plus
    #     haut) : retire la relation standard directe MTA<->pare-feu pour
    #     les nœuds explicitement rerouté, ajoute les maillons déclarés à
    #     la place. ---
    if email_flow_removals or email_flow_extra_flows:
        _last_equipment_id_flt = network_equipment_raw[-1]["id"] if network_equipment_raw else None
        _filtered_flows = []
        for f in raw_flows:
            if f["category"] == "smtp":
                if ("from", f["from"]) in email_flow_removals and f["to"] == _last_equipment_id_flt:
                    continue
                if ("to", f["to"]) in email_flow_removals and f["from"] == _last_equipment_id_flt:
                    continue
            _filtered_flows.append(f)
        raw_flows = _filtered_flows + email_flow_extra_flows

    # --- Exclusions PUREMENT VISUELLES sur les schémas (le flux existe
    #     réellement et reste dans la matrice exhaustive de fin de document
    #     --- seul son tracé sur les schémas est masqué). Section dédiée en
    #     fin de fichier de configuration client, appariement des nœuds
    #     dans n'importe quel sens. ---
    diagram_exclusion_pairs = set()
    for ex in config.get("flow_diagram_exclusions", []) or []:
        if not isinstance(ex, dict):
            continue
        n1, n2, cat = ex.get("node1", ""), ex.get("node2", ""), ex.get("category", "")
        diagram_exclusion_pairs.add((n1, n2, cat))
        diagram_exclusion_pairs.add((n2, n1, cat))

    def excluded_from_diagrams(f):
        return (f["from"], f["to"], f["category"]) in diagram_exclusion_pairs

    # --- Catégories dont le schéma dédié doit être généré (protocol_schemas
    #     dans la config client --- simple Oui/Non par catégorie ; par
    #     défaut Oui si non précisé). ---
    protocol_schemas_raw = config.get("protocol_schemas", {}) or {}

    # --- Enrichissement des flux (labels + résolution de catégorie/couleur,
    #     calculés sur les données brutes ; le schéma TikZ est généré AVANT
    #     tout échappement destiné à l'affichage en prose/tableaux, pour
    #     éviter un double échappement) ---
    used_category_ids = []
    flows = []
    for f in raw_flows:
        f = dict(f)
        f["from_label"] = label_for(f["from"])
        f["to_label"] = label_for(f["to"])
        f.setdefault("protocol", "")
        cat_id = f.get("category") or "other"
        cat_meta = flow_categories.get(cat_id, flow_categories["other"])
        f["category"] = cat_id
        f["category_label_raw"] = cat_meta.get("label", cat_id)
        f["color_name"] = _safe_color_name(cat_id)
        f["_diagram_excluded"] = excluded_from_diagrams(f)
        if cat_id not in used_category_ids:
            used_category_ids.append(cat_id)
        flows.append(f)

    # --- Couleurs de catégories effectivement utilisées : \definecolor +
    #     entrées de légende, dans l'ordre du catalogue (pas l'ordre YAML
    #     du client, pour une légende stable et prévisible). ---
    used_category_ids_ordered = sorted(
        used_category_ids,
        key=lambda cid: flow_categories.get(cid, flow_categories["other"]).get("order", 999),
    )
    color_def_lines = []
    legend_entries = []
    flow_category_ref = []
    for cid in used_category_ids_ordered:
        meta = flow_categories.get(cid, flow_categories["other"])
        color_name = _safe_color_name(cid)
        color_def_lines.append(f"\\definecolor{{{color_name}}}{{HTML}}{{{meta.get('color', '2E74B5')}}}")
        legend_entries.append((color_name, meta.get("label", cid)))
        flow_category_ref.append({
            "color_name": color_name,
            "label": esc(meta.get("label", cid)),
            "typical_ports": esc(meta.get("typical_ports", "")),
        })
    flow_category_color_defs = "\n".join(color_def_lines)

    # --- Schéma réseau dynamique (vue d'ensemble) : généré sur les données
    #     BRUTES, SANS les flèches de flux (volontairement omises pour ne
    #     garder qu'une vue topologique claire ; le détail des flux est
    #     donné par les schémas par catégorie ci-dessous et par la matrice
    #     de flux en fin de document). ---
    diagram_tikz = build_tikz(
        zones, nodes_raw, [],
        network_equipment=network_equipment_raw,
        legend_entries=[],
    )

    # --- Un schéma par catégorie de flux effectivement utilisée, pour ne
    #     pas surcharger le schéma d'ensemble. Mêmes positions de nœuds que
    #     le schéma global (déterministe), seuls les flux de la catégorie
    #     concernée sont tracés. ---
    category_diagrams = []
    if len(used_category_ids_ordered) >= 1:
        for cid in used_category_ids_ordered:
            if protocol_schemas_raw.get(cid, True) is False:
                continue  # schéma dédié désactivé pour cette catégorie (protocol_schemas)
            meta = flow_categories.get(cid, flow_categories["other"])
            color_name = _safe_color_name(cid)
            cat_flows = [f for f in flows if f["category"] == cid and not f["_diagram_excluded"]]
            if not cat_flows:
                continue
            cat_tikz = build_tikz(
                zones, nodes_raw, cat_flows,
                network_equipment=network_equipment_raw,
                legend_entries=[],
            )
            category_diagrams.append({
                "tikz": cat_tikz,
                "label": esc(meta.get("label", cid)),
                "color_name": color_name,
            })

    # --- À partir d'ici, on échappe les champs texte pour un usage en
    #     prose / tableaux LaTeX classiques (le schéma est déjà généré) ---
    nodes = []
    nodes_by_raw_id = {}
    for n in nodes_raw:
        n = dict(n)
        _raw_id = n["id"]
        zone = zones_by_id.get(n["zone"], {})
        n["zone_label"] = esc(zone.get("label", n["zone"]))
        n["components_display"] = esc(n.get("components_display", ""))
        n["id"] = esc(n["id"])
        n["hostname"] = esc(n.get("hostname", ""))
        n["ip"] = esc(n.get("ip", ""))
        n["public_ip"] = esc(n.get("public_ip", ""))
        n["dkim_carrier_domains"] = ""  # rempli plus bas si ce nœud porte le DKIM d'un ou plusieurs domaines
        ms = n.get("mailstore") or {}
        n["mailstore_backup_retention"] = esc(f"{ms['backup_retention_days']} jours") if ms.get("backup_retention_days") is not None else ""
        n["mailstore_hsm_enabled"] = bool(ms.get("hsm_enabled"))
        n["mailstore_hot_retention"] = esc(f"{ms['hot_data_retention_days']} jours") if ms.get("hot_data_retention_days") is not None else ""
        n["mailstore_hsm_target"] = esc(ms.get("hsm_target", ""))

        backup_raw = n.get("backup") or {}
        n["backup_enabled_display"] = _oui_non(backup_raw.get("enabled"), default="Non")
        schedule_lines = []
        for entry in backup_raw.get("schedule", []) or []:
            days = entry.get("days", "")
            times = ", ".join(entry.get("times", []) or [])
            schedule_lines.append(f"{days} : {times}")
        n["backup_schedule_display"] = esc("; ".join(schedule_lines)) if schedule_lines else ""
        nodes.append(n)
        nodes_by_raw_id[_raw_id] = n

    for f in flows:
        f["label"] = esc(f.get("label", ""))
        f["protocol"] = esc(f.get("protocol", ""))
        f["category_label"] = esc(f.get("category_label_raw", ""))
        ports_list = f.get("ports") or []
        if ports_list:
            f["ports_display"] = esc(", ".join(f"{p.get('proto', 'TCP')}/{p.get('port', '?')}" for p in ports_list))
        else:
            f["ports_display"] = f["label"] or "[à préciser]"

    # --- Composants activés, triés par "order" du catalogue ---
    load_balancing_raw = config.get("load_balancing", {}) or {}
    components = []
    for comp_id, meta in sorted(catalog.items(), key=lambda kv: kv[1].get("order", 999)):
        if not services.get(comp_id):
            continue
        comp_nodes = [n for n in nodes if comp_id in (n.get("components") or [])]
        comp = esc_dict(meta)
        comp["id"] = comp_id
        comp["nodes"] = comp_nodes
        comp["packages_list"] = [escape_latex(p.strip()) for p in meta.get("packages", "").split(",")]
        comp["load_balancing"] = esc(load_balancing_raw.get(comp_id, ""))
        if comp_id == "mailbox":
            comp["hsm_nodes"] = [n for n in comp_nodes if n.get("mailstore_hsm_enabled")]
        components.append(comp)

    # --- Références croisées LDAP Master / Replica (pour les templates
    #     directory_master.tex.j2 / directory_replica.tex.j2) ---
    ldap_master_nodes = [n for n in nodes if "directory_master" in (n.get("components") or [])]
    ldap_replica_nodes = [n for n in nodes if "directory_replica" in (n.get("components") or [])]

    # --- Liste "périmètre / services rendus" (utilisée en §1.3 Périmètre) ---
    scope_items = []
    for comp_id, meta in sorted(scope_catalog.items(), key=lambda kv: kv[1].get("order", 999)):
        if services.get(comp_id):
            scope_items.append(esc(meta["text"]))

    # --- Services rendus aux utilisateurs (§3.1) : descriptions orientées
    #     usage final, une entrée par brique perçue par l'utilisateur (le
    #     LDAP/l'infrastructure n'y apparaissent volontairement pas). ---
    user_service_items = []
    for svc_id, meta in sorted(user_services_catalog.items(), key=lambda kv: kv[1].get("order", 999)):
        if services.get(meta.get("trigger")):
            user_service_items.append({"name": esc(meta["name"]), "text": esc(meta["text"])})

    # --- Protocoles d'accès autorisés, déduits des composants activés
    #     (pas de champ de config dédié : c'est une conséquence directe des
    #     rôles présents sur la plateforme). ---
    allowed_protocols = []
    if services.get("proxy"):
        allowed_protocols += ["HTTPS (webmail)", "IMAPS", "POP3S", "ActiveSync (EAS, mobilité)"]
    if services.get("mta_auth"):
        allowed_protocols.append("SMTP submission authentifié (587)")
    allowed_protocols = [esc(p) for p in allowed_protocols]

    # --- Historique des révisions (par défaut si non fourni) ---
    client_raw = config["client"]
    revisions = config.get("revisions") or [
        {"version": "0.1", "date": "[date]", "author": client_raw.get("author", "[auteur]"), "note": "Création initiale"},
        {"version": "1.0", "date": "[date]", "author": client_raw.get("author", "[auteur]"), "note": "Version générée automatiquement"},
    ]
    revisions = esc_list_of_dicts(revisions, "note")

    # "Version du document"/"Date" sur la couverture ne sont plus des
    # champs saisis séparément dans client: --- ils reprennent la
    # dernière entrée de l'historique des révisions ci-dessus, pour
    # n'avoir qu'un seul endroit à mettre à jour à chaque nouvelle version
    # du document.
    _latest_revision = revisions[-1] if revisions else {"version": "1.0", "date": "[à préciser]"}
    client["version"] = _latest_revision["version"]
    client["date"] = _latest_revision["date"]

    # --- Annexes : simple table de documents associés ---
    annexes_ctx = esc_list_of_dicts(config.get("annexes", []), "name")

    # --- Opérations planifiées (crons), tous nœuds confondus ---
    scheduled_operations_ctx = []
    for op in config.get("scheduled_operations", []) or []:
        lines = []
        for entry in op.get("schedule", []) or []:
            days = entry.get("days", "")
            times = ", ".join(entry.get("times", []) or [])
            lines.append(f"{days} : {times}")
        scheduled_operations_ctx.append({
            "node": esc(op.get("node", "")),
            "operation": esc(op.get("operation", "")),
            "schedule_display": esc("; ".join(lines)) if lines else "",
        })

    # --- Interfaces et intégrations : chapitre entièrement omis si la
    #     liste est vide (le paramétrage reste disponible pour un usage
    #     futur, sans forcer l'affichage d'exemples génériques). ---
    interfaces_ctx = esc_list_of_dicts(config.get("interfaces", []), "system")

    # --- Solution Carbonio : produit + licence ---
    product_raw = config.get("product", {})
    product = {
        "version": esc(product_raw.get("version", "[à préciser]")),
        "release_date": esc(product_raw.get("release_date", "[à préciser]")),
        "version_check_url": product_raw.get("version_check_url", "https://docs.zextras.com/en/carbonio-release-notes/latest"),
        "user_doc_url": product_raw.get("user_doc_url", "https://docs.zextras.com/en/user-guide"),
        "admin_doc_url": product_raw.get("admin_doc_url", "https://docs.zextras.com/en/carbonio-admin-guide"),
    }
    license_raw = config.get("license", {})
    license_ctx = {
        "accounts": esc(str(license_raw.get("accounts", "[à préciser]"))),
        "activesync": esc(str(license_raw.get("activesync", "[à préciser]"))),
        "chat": _oui_non(license_raw.get("chat")),
        "two_fa": _oui_non(license_raw.get("two_fa")),
        "s3_storage": _oui_non(license_raw.get("s3_storage")),
        "video": _oui_non(license_raw.get("video")),
        "files": _oui_non(license_raw.get("files")),
    }

    # --- DNS : organisé PAR DOMAINE (un domaine peut avoir plusieurs
    #     enregistrements MX, mais un seul SPF/DKIM/DMARC en général). ---
    dns_raw = config.get("dns", {})
    domains_raw_list = [d for d in dns_raw.get("domains", []) if isinstance(d, dict)]

    def build_domain_auth(d):
        """Authentification pour un domaine principal --- jamais calculée
        pour un alias de domaine (pas de comptes propres, donc pas
        d'authentification propre à ce niveau)."""
        auth_raw = d.get("authentication", {}) or {}
        methods = auth_raw.get("methods") or ["native"]
        ext_ldap_raw = auth_raw.get("external_ldap", {}) or {}
        saml2_raw = auth_raw.get("saml2", {}) or {}
        return {
            "methods": methods,
            "methods_display": [esc(AUTH_METHOD_LABELS.get(m, m)) for m in methods],
            "has_external_ldap": "external_ldap" in methods,
            "external_ldap": {
                "fallback_to_native": _oui_non(ext_ldap_raw.get("fallback_to_native"), default="Non"),
                # Plusieurs serveurs possibles pour un même domaine (répartition
                # de charge / haute disponibilité de l'annuaire externe).
                "servers": esc_list_of_dicts(ext_ldap_raw.get("servers", []), "hostname"),
            },
            "has_saml2": "saml2" in methods,
            "saml2": {
                "idp_metadata_url": esc(saml2_raw.get("idp_metadata_url", "[à préciser]")),
            },
        }

    def build_domain_entry(d):
        domain_raw = d.get("domain", "")
        mx_records_raw = d.get("mx_records") or []
        has_mx = bool(mx_records_raw)
        has_spf = bool(d.get("spf"))
        has_dkim = bool(d.get("dkim_selector"))
        has_dmarc = bool(d.get("dmarc"))
        missing = []
        if not has_mx:
            missing.append("MX")
        if not has_spf:
            missing.append("SPF")
        if not has_dkim:
            missing.append("DKIM")
        if not has_dmarc:
            missing.append("DMARC")

        # --- Porteur de la signature DKIM pour ce domaine --- absent =
        #     Carbonio (MTA OUT, comportement historique) ; "antispam_antivirus"
        #     = l'AS/AV configuré ; ou un id de nœud/pool précis (ex. un
        #     relais tiers). Une seule déclaration, ici, alimente à la fois
        #     ce tableau, le récapitulatif AS/AV et la section du nœud
        #     porteur lui-même --- voir dkim_carrier_domains_by_raw_id plus
        #     bas.
        dkim_carrier_token = d.get("dkim_carrier")
        dkim_carrier_warning = None
        dkim_carrier_member_ids = []
        if not dkim_carrier_token:
            dkim_carrier = "Carbonio (MTA OUT)"
        elif dkim_carrier_token == "antispam_antivirus":
            asav_name_raw = asav_raw.get("name", "").strip()
            dkim_carrier = f"AS/AV ({asav_name_raw})" if asav_name_raw else "AS/AV"
        else:
            _members, _exists = _resolve_node_or_pool(dkim_carrier_token)
            if not _exists:
                dkim_carrier = f"« {dkim_carrier_token} » (INCONNU)"
                dkim_carrier_warning = (
                    f"le porteur DKIM déclaré pour ce domaine (« {esc(dkim_carrier_token)} ») ne correspond "
                    f"à aucun nœud ni pool déclaré --- vérifier load_balancer_pools et les identifiants de nœuds."
                )
            else:
                dkim_carrier_member_ids = _members
                dkim_carrier = dkim_carrier_token if dkim_carrier_token not in load_balancer_pools_raw \
                    else f"{dkim_carrier_token} ({', '.join(_members)})"

        # Bonne pratique : si l'AS/AV filtre le sortant mais ne porte pas
        # lui-même le DKIM de ce domaine, la signature n'est pas apposée
        # au bon endroit de la chaîne d'émission --- à signaler.
        dkim_best_practice_warning = None
        if asav_outbound_filtering_bool and dkim_carrier_token != "antispam_antivirus":
            dkim_best_practice_warning = (
                "l'AS/AV filtre les e-mails sortants pour cette plateforme, mais ne porte pas la "
                "signature DKIM de ce domaine --- la signature devrait normalement être apposée "
                "avant tout traitement/relais sortant supplémentaire (bonne pratique)."
            )

        is_alias = bool(d.get("alias_of"))
        return {
            "domain": esc(domain_raw),
            "alias_of": esc(d.get("alias_of", "")),
            "is_alias": is_alias,
            "mx_records": esc_list_of_dicts(mx_records_raw, "hostname"),
            "has_mx": has_mx,
            "spf": esc(d.get("spf", "")),
            "has_spf": has_spf,
            "dkim_selector": esc(d.get("dkim_selector", "")),
            "has_dkim": has_dkim,
            "dkim_carrier": esc(dkim_carrier),
            "dkim_carrier_token": dkim_carrier_token,
            "dkim_carrier_member_ids": dkim_carrier_member_ids,
            "dkim_carrier_warning": dkim_carrier_warning,
            "dkim_best_practice_warning": dkim_best_practice_warning,
            "dmarc": esc(d.get("dmarc", "")),
            "has_dmarc": has_dmarc,
            "missing_display": esc(", ".join(missing)) if missing else "",
            # Jamais configurable sur un alias (pas de comptes propres) ---
            # voir build_domain_auth().
            "authentication": None if is_alias else build_domain_auth(d),
            "aliases": [],
        }

    # Deux passes : construire toutes les entrées, puis rattacher chaque
    # alias (champ "alias_of") à son domaine principal --- un alias devient
    # une sous-section du domaine auquel il est attaché plutôt qu'une entrée
    # de premier niveau.
    entries_by_domain = {}
    ordered_raw_domains = []
    for d in domains_raw_list:
        entry = build_domain_entry(d)
        entries_by_domain[d.get("domain", "")] = entry
        ordered_raw_domains.append(d)

    dns_domains = []
    for d in ordered_raw_domains:
        domain_raw = d.get("domain", "")
        entry = entries_by_domain[domain_raw]
        alias_of_raw = d.get("alias_of")
        if alias_of_raw:
            parent = entries_by_domain.get(alias_of_raw)
            if parent is not None:
                parent["aliases"].append(entry)
                continue
            # Alias déclaré mais domaine principal introuvable dans la
            # config : on le garde visible au premier niveau plutôt que de
            # le faire disparaître silencieusement.
        dns_domains.append(entry)

    dns_ctx = {"domains": dns_domains}

    # --- Une fois tous les domaines connus (y compris les alias, qui ont
    #     leur propre porteur DKIM potentiel) : calcule le récapitulatif
    #     AS/AV, et injecte sur chaque nœud/pool porteur la liste des
    #     domaines dont il porte la signature DKIM (affiché dans sa propre
    #     section de composant, ex. mail_relay.tex.j2). ---
    _all_domain_entries = list(entries_by_domain.values())
    _asav_dkim_domains = sorted({e["domain"] for e in _all_domain_entries if e["dkim_carrier_token"] == "antispam_antivirus"})
    antispam_antivirus_ctx["dkim_domains_display"] = (
        ", ".join(_asav_dkim_domains) if _asav_dkim_domains
        else "Aucun --- Carbonio gère le DKIM pour tous les domaines"
    )

    dkim_carrier_domains_by_raw_id = {}
    for e in _all_domain_entries:
        for _node_id in e.get("dkim_carrier_member_ids") or []:
            dkim_carrier_domains_by_raw_id.setdefault(_node_id, []).append(e["domain"])
    for _node_id, _domains in dkim_carrier_domains_by_raw_id.items():
        _node_obj = nodes_by_raw_id.get(_node_id)
        if _node_obj is not None:
            _node_obj["dkim_carrier_domains"] = ", ".join(_domains)

    # --- Auto-provisionnement (section entièrement conditionnelle) ---
    autoprov_raw = config.get("autoprovisioning", {}) or {}
    autoprovisioning_enabled = bool(autoprov_raw.get("enabled"))
    ldap_srv = autoprov_raw.get("ldap_server", {}) or {}
    autoprovisioning_ctx = {
        "node": esc(autoprov_raw.get("node", "[à préciser]")),
        "script_name": esc(autoprov_raw.get("script_name", "[à préciser]")),
        "ldap_server_hostname": esc(ldap_srv.get("hostname", "[à préciser]")),
        "ldap_server_ip": esc(ldap_srv.get("ip", "[à préciser]")),
        "arguments": esc(autoprov_raw.get("arguments", "")),
        "frequency": esc(autoprov_raw.get("frequency", "[à préciser]")),
        "sync_accounts": _oui_non(autoprov_raw.get("sync_accounts"), default="Non"),
        "sync_distribution_lists": _oui_non(autoprov_raw.get("sync_distribution_lists"), default="Non"),
        "sync_resources": _oui_non(autoprov_raw.get("sync_resources"), default="Non"),
        "sync_signatures": _oui_non(autoprov_raw.get("sync_signatures"), default="Non"),
    }

    # --- Authentification : connexion (vhost/domaine par défaut),
    #     politiques de mots de passe/verrouillage (plusieurs possibles,
    #     chacune avec sa portée --- Plateforme, COS, ou Domaine ---
    #     puisqu'une politique unique et globale n'est qu'un cas
    #     particulier), et protection anti brute-force. La méthode
    #     d'authentification (native/LDAP externe/SAML2) est un attribut
    #     de CHAQUE DOMAINE, pas de cette section globale --- voir
    #     build_domain_auth() et dns_ctx. ---
    auth_raw = config.get("authentication", {}) or {}
    connection_raw = auth_raw.get("connection", {}) or {}
    brute_force_raw = auth_raw.get("brute_force_protection", {}) or {}
    password_policies_raw = auth_raw.get("password_policies", []) or []
    authentication_ctx = {
        "connection": {
            "vhost": esc(connection_raw.get("vhost", "[à préciser]")),
            "url": connection_raw.get("url", ""),
            "default_domain": esc(connection_raw.get("default_domain", "[à préciser]")),
        },
        "password_policies": [
            {
                "scope": esc(p.get("scope", "[à préciser]")),
                "password_policy": esc(p.get("password_policy", "[à préciser]")),
                "lockout_policy": esc(p.get("lockout_policy", "[à préciser]")),
            }
            for p in password_policies_raw if isinstance(p, dict)
        ],
        "brute_force_protection": {
            "enabled": _oui_non(brute_force_raw.get("enabled"), default="Non"),
            "tool": esc(brute_force_raw.get("tool", "")),
            "details": esc(brute_force_raw.get("details", "")),
        },
    }

    # --- Support ---
    support_raw = config.get("support", {})
    support_ctx = {
        "url": support_raw.get("url", "https://support.zextras-services.fr"),
        "phone": esc(support_raw.get("phone", "[à préciser]")),
        "escalation_name": esc(support_raw.get("escalation_name", "[à préciser]")),
        "escalation_phone": esc(support_raw.get("escalation_phone", "[à préciser]")),
    }

    # --- PCA / PRA : deux indicateurs Oui/Non distincts, chacun avec un
    #     texte de procédure par défaut si aucun PCA/PRA spécifique. ---
    pca_pra_defaults = load_yaml(TEMPLATES_DIR / "pca_pra_defaults.yaml")
    pca_raw = config.get("pca", {}) or {}
    pra_raw = config.get("pra", {}) or {}
    pca_ctx = {
        "enabled": bool(pca_raw.get("enabled")),
        "enabled_display": _oui_non(pca_raw.get("enabled"), default="Non"),
        "description": esc(pca_raw.get("description", "")),
    }
    pra_ctx = {
        "enabled": bool(pra_raw.get("enabled")),
        "enabled_display": _oui_non(pra_raw.get("enabled"), default="Non"),
        "description": esc(pra_raw.get("description", "")),
        "rto": esc(pra_raw.get("rto", "[à préciser]")),
        "rpo": esc(pra_raw.get("rpo", "[à préciser]")),
        "secondary_site": esc(pra_raw.get("secondary_site", "[à préciser]")),
    }
    pca_pra_defaults_ctx = {
        "pca_default": pca_pra_defaults.get("pca_default", ""),
        "pra_default": pca_pra_defaults.get("pra_default", ""),
    }

    component_groups_ctx = {
        gid: {"name": esc(meta["name"]), "intro": esc(meta["intro"])}
        for gid, meta in component_groups.items()
    }

    # --- Parties prenantes : client et intégrateur (Zextras Services) ---
    stakeholder_client = _build_stakeholder_ctx(
        config.get("client", {}), esc, outdir, config_dir, "client_logo",
    )
    stakeholder_integrator = _build_stakeholder_ctx(
        config.get("integrator", {}), esc, outdir, config_dir, "integrator_logo",
        default_logo=DEFAULT_INTEGRATOR_LOGO,
    )

    return {
        "client": client,
        "confidentiality": client["confidentiality"],
        "carbonio_edition": carbonio_edition,
        "carbonio_edition_label": carbonio_edition_label,
        "sla": sla,
        "services": services,
        "zones": zones,
        "nodes": nodes,
        "flows": flows,
        "components": components,
        "component_groups": component_groups_ctx,
        "stakeholder_client": stakeholder_client,
        "stakeholder_integrator": stakeholder_integrator,
        "ldap_master_nodes": ldap_master_nodes,
        "ldap_replica_nodes": ldap_replica_nodes,
        "scope_items": scope_items,
        "user_service_items": user_service_items,
        "allowed_protocols": allowed_protocols,
        "antispam_antivirus": antispam_antivirus_ctx,
        "interfaces": interfaces_ctx,
        "scheduled_operations": scheduled_operations_ctx,
        "annexes": annexes_ctx,
        "diagram_tikz": diagram_tikz,
        "category_diagrams": category_diagrams,
        "flow_category_color_defs": flow_category_color_defs,
        "flow_category_ref": flow_category_ref,
        "revisions": revisions,
        "product": product,
        "license": license_ctx,
        "dns": dns_ctx,
        "autoprovisioning_enabled": autoprovisioning_enabled,
        "autoprovisioning": autoprovisioning_ctx,
        "authentication": authentication_ctx,
        "support": support_ctx,
        "pca": pca_ctx,
        "pra": pra_ctx,
        "pca_pra_defaults": pca_pra_defaults_ctx,
        "config_filename": esc(config_filename),
        "generation_date": datetime.date.today().strftime("%d/%m/%Y"),
    }


def render_component(env, comp, ctx):
    template_name = f"{comp['id']}.tex.j2"
    if (COMPONENTS_DIR / template_name).exists():
        tmpl = env.get_template(template_name)
    else:
        tmpl = env.get_template("_generic.tex.j2")
    local_ctx = dict(ctx)
    local_ctx["comp"] = comp
    return tmpl.render(**local_ctx)


def assemble_body(env, ctx):
    """Assemble le corps du document (hors préambule) à partir d'un contexte
    déjà construit. Isolé de `assemble_document` pour pouvoir être rejoué
    une seconde fois avec un contexte légèrement modifié (ex. export ODT,
    qui substitue les schémas TikZ par des images pré-rendues)."""
    body_parts = []
    for entry in STATIC_PARTIALS:
        if entry == "__TOC__":
            body_parts.append(r"\clearpage" + "\n" + r"\tableofcontents" + "\n" + r"\clearpage")
        elif entry == "__COMPONENTS__":
            rendered_groups = set()
            for comp in ctx["components"]:
                if comp["id"] == "monitoring":
                    continue  # rendu séparément en fin de document (chapitre dédié)
                group_id = comp.get("group")
                if group_id:
                    if group_id not in rendered_groups:
                        rendered_groups.add(group_id)
                        group_meta = ctx["component_groups"].get(group_id)
                        if group_meta:
                            body_parts.append(f"\\subsection{{{group_meta['name']}}}\n{group_meta['intro']}")
                    body_parts.append(f"\\subsubsection{{{comp['name']}}}")
                else:
                    body_parts.append(f"\\subsection{{{comp['name']}}}")
                body_parts.append(render_component(env, comp, ctx))
        elif entry == "__MONITORING__":
            if ctx.get("services", {}).get("monitoring"):
                tmpl = env.get_template("monitoring.tex.j2")
                body_parts.append(tmpl.render(**ctx))
        elif entry == "__INTERFACES__":
            if ctx.get("interfaces"):
                tmpl = env.get_template("interfaces.tex.j2")
                body_parts.append(tmpl.render(**ctx))
        elif entry == "__AUTOPROVISIONING__":
            if ctx.get("autoprovisioning_enabled"):
                tmpl = env.get_template("autoprovisioning.tex.j2")
                body_parts.append(tmpl.render(**ctx))
        else:
            tmpl = env.get_template(entry)
            body_parts.append(tmpl.render(**ctx))
            if entry == "cover.tex.j2":
                body_parts.append(r"\clearpage")

    return "\n\n".join(body_parts)


def assemble_document(config, config_filename, outdir=None, config_dir=None):
    env = make_env()
    ctx = build_context(config, config_filename, outdir=outdir, config_dir=config_dir)
    preamble = env.get_template("preamble.tex.j2").render(**ctx)
    body = assemble_body(env, ctx)
    doc = preamble + "\n\n\\begin{document}\n\n" + body + "\n\n\\end{document}\n"
    return doc, env, ctx


def compile_pdf(tex_path: Path, outdir: Path):
    for i in range(2):
        result = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-output-directory", str(outdir), str(tex_path)],
            cwd=str(outdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    log_path = tex_path.with_suffix(".log")
    ok = tex_path.with_suffix(".pdf").exists()
    if not ok:
        print("!!! La compilation LaTeX a échoué. Extrait du log :", file=sys.stderr)
        if log_path.exists():
            print("\n".join(log_path.read_text(errors="ignore").splitlines()[-60:]), file=sys.stderr)
    return ok, result


def main():
    parser = argparse.ArgumentParser(description="Génère un DAT Carbonio à partir d'une config YAML.")
    parser.add_argument("config", help="Chemin vers le fichier de configuration client (YAML)")
    parser.add_argument("--outdir", default="build/customers", help="Répertoire racine de sortie (défaut: build/customers) --- le document est écrit dans <outdir>/<nom_court_client>/")
    parser.add_argument("--compile", action="store_true", help="Compiler le .tex en PDF via pdflatex")
    parser.add_argument("--name", default=None, help="Nom de base du fichier généré (défaut: dérivé du client)")
    parser.add_argument(
        "--update-dns", action="store_true",
        help="Avant de générer, met à jour MX/SPF/DMARC du fichier de config depuis le DNS réel "
             "(voir update_dns_from_zone.py --- jamais le DKIM, jamais en écrasant une valeur "
             "existante si la résolution échoue)."
    )
    args = parser.parse_args()

    config_path = Path(args.config)

    if args.update_dns:
        from update_dns_from_zone import update_dns_from_zone
        update_dns_from_zone(config_path)
        print()  # ligne vide de séparation avant la suite de la génération

    config = load_yaml(config_path)

    # Un dossier par client (nom court, ex. "build/customers/Exemple_SA/"),
    # avec un sous-dossier "generation" pour les fichiers intermédiaires
    # LaTeX (.tex/.aux/.log/.out/.toc, logos copiés...) --- le PDF final
    # est copié à la racine du dossier client, seul fichier qu'un
    # opérateur a besoin de voir au premier coup d'œil.
    outdir_base = BASE_DIR / args.outdir
    client_folder = config["client"]["name"].replace(" ", "_")
    client_dir = outdir_base / client_folder
    generation_dir = client_dir / "generation"
    generation_dir.mkdir(parents=True, exist_ok=True)

    doc, env, ctx = assemble_document(config, config_path.name, outdir=generation_dir, config_dir=config_path.parent)

    base_name = args.name or ("DAT_" + config["client"]["name"].replace(" ", "_"))
    tex_path = generation_dir / f"{base_name}.tex"
    tex_path.write_text(doc, encoding="utf-8")
    print(f"[OK] Document LaTeX généré : {tex_path}")

    if args.compile:
        ok, result = compile_pdf(tex_path, generation_dir)
        if ok:
            final_pdf = client_dir / f"{base_name}.pdf"
            shutil.copyfile(tex_path.with_suffix(".pdf"), final_pdf)
            print(f"[OK] PDF généré : {final_pdf}")
        else:
            print("[ERREUR] Échec de la compilation LaTeX.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
