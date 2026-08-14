#!/usr/bin/env python3
"""
Génère un Document d'Exploitation (DEX) Carbonio à partir de fichiers
"brique" auto-découverts dans le dossier briques/.

Deux modes de génération :

  python3 generate_dex.py --compile
      Mode générique : toutes les briques, aucun nœud listé, pas de
      parties prenantes, confidentialité "Public" par défaut. Document de
      référence valable pour n'importe quelle infrastructure Carbonio.

  python3 generate_dex.py --client config/client.yaml --compile
      Mode client : ne garde que les briques dont au moins un service
      listé est activé chez ce client (les briques sans champ "services"
      sont universelles et toujours incluses), liste les nœuds concernés
      par chaque brique (champ "components"), ajoute le chapitre "Parties
      prenantes" (réutilisé du DAT) et un paragraphe de propriété
      intellectuelle, confidentialité "Client" par défaut.

Principe inchangé : AUCUNE brique ni opération n'est codée en dur dans ce
script. Voir briques/*.yaml pour le détail des deux schémas disponibles
("operations" et "reference_table").
"""
import argparse
import datetime
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from tikz_builder import escape_latex
import generate_dat

BASE_DIR = Path(__file__).resolve().parent
BRIQUES_DIR = BASE_DIR / "briques"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DEX_DIR = BASE_DIR / "templates_dex"
CARBONIO_EDITIONS_PATH = TEMPLATES_DIR / "carbonio_editions.yaml"

CONFIDENTIALITY_LABELS = {
    "public": "Public",
    "client": "Client",
    "restreint": "Restreint",
    "confidentiel": "Confidentiel",
}


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def esc(v):
    return escape_latex(v) if isinstance(v, str) else v


def make_env():
    # Cherche d'abord dans templates_dex/ (et son sous-dossier partials/),
    # puis dans templates/ --- ce qui permet de réutiliser directement les
    # fichiers du DAT (preamble.tex.j2, partials/stakeholders.tex.j2) sans
    # les dupliquer.
    return Environment(
        loader=FileSystemLoader([
            str(TEMPLATES_DEX_DIR), str(TEMPLATES_DEX_DIR / "partials"),
            str(TEMPLATES_DIR), str(TEMPLATES_DIR / "partials"),
        ]),
        block_start_string="\\BLOCK{", block_end_string="}",
        variable_start_string="\\VAR{", variable_end_string="}",
        comment_start_string="\\#{", comment_end_string="}",
        trim_blocks=True,
        autoescape=False,
    )


RAW_CAPABLE_FIELDS = ["description", "prerequisites", "explanation", "warning"]


def _field_with_raw_option(op, field, op_title, warnings):
    """Un champ texte peut être fourni en version échappée (`champ:`,
    sûre par défaut) ou en version LaTeX brute (`champ_raw:`, insérée
    telle quelle --- gras, listes, macros... possibles, mais la syntaxe
    LaTeX devient la responsabilité de l'auteur). Un garde-fou léger
    (accolades non balancées) émet un avertissement --- jamais un blocage
    --- pour repérer une faute de frappe évidente avant compilation."""
    raw_val = op.get(field + "_raw")
    if raw_val is not None:
        raw_val = str(raw_val)
        opens, closes = raw_val.count("{"), raw_val.count("}")
        if opens != closes:
            warnings.append(
                f"[ATTENTION] Opération « {op_title} » --- champ '{field}_raw' : "
                f"accolades non balancées ({opens} '{{' / {closes} '}}'). Vérifier la syntaxe LaTeX."
            )
        return raw_val
    return esc(op.get(field, ""))


def _escape_operation(op, warnings):
    """Échappe les champs texte normaux d'une opération --- PAS les champs
    verbatim (commands/example_output), qui passent par `lstlisting` et
    n'ont donc besoin d'aucun échappement LaTeX. Chaque champ texte
    accepte une variante `_raw` (voir _field_with_raw_option)."""
    out = dict(op)
    out["title"] = esc(op.get("title", ""))
    op_title_for_warnings = out["title"] or "(sans titre)"
    for field in RAW_CAPABLE_FIELDS:
        out[field] = _field_with_raw_option(op, field, op_title_for_warnings, warnings)
    out["bullet_items"] = [esc(it) for it in op.get("items", []) or []]
    out["options_table"] = [
        {"option": esc(row.get("option", "")), "description": esc(row.get("description", ""))}
        for row in (op.get("options_table") or [])
        if isinstance(row, dict)
    ]
    commands = [str(c) for c in (op.get("commands") or [])]
    out["commands"] = commands
    out["commands_joined"] = "\n".join(commands)
    out["example_output"] = op.get("example_output", "") or ""

    attrs_raw = op.get("attributes")
    out["attributes"] = None
    if isinstance(attrs_raw, dict):
        out["attributes"] = {
            "type": esc(attrs_raw.get("type", "")),
            "frequency": esc(attrs_raw.get("frequency", "")),
            "criticality": esc(attrs_raw.get("criticality", "")),
            "automatable": esc(attrs_raw.get("automatable", "")),
            "interruption": esc(attrs_raw.get("interruption", "")),
            "expected_control": esc(attrs_raw.get("expected_control", "")),
            "estimated_duration": esc(attrs_raw.get("estimated_duration", "")),
            "recommended_window": esc(attrs_raw.get("recommended_window", "")),
        }
    return out


def build_briques_context(services_enabled, nodes_by_component, client_mode, carbonio_edition, ce_restrictions, warnings):
    """Charge et échappe toutes les briques auto-découvertes, triées par
    nom de fichier. En mode client, filtre sur `services:` (brique
    universelle si le champ est absent), retire les briques dont la
    fonctionnalité (`ce_feature:`) est indisponible dans l'édition
    Carbonio du client, et résout `components:` en liste de nœuds
    concernés."""
    briques = []
    for path in sorted(BRIQUES_DIR.glob("*.yaml")):
        raw = load_yaml(path)

        required_services = raw.get("services") or []
        if client_mode and required_services:
            if not any(services_enabled.get(s) for s in required_services):
                continue  # aucun service requis n'est activé chez ce client

        ce_feature = raw.get("ce_feature")
        if client_mode and ce_feature and carbonio_edition == "ce":
            feature_meta = ce_restrictions.get(ce_feature, {})
            if feature_meta.get("ce_available") is False:
                continue  # fonctionnalité absente de la Community Edition

        concerned_nodes = []
        if client_mode:
            seen = set()
            for comp_id in (raw.get("components") or []):
                for node_id in nodes_by_component.get(comp_id, []):
                    if node_id not in seen:
                        seen.add(node_id)
                        concerned_nodes.append(node_id)

        brique = {
            "name": esc(raw.get("brique", path.stem)),
            "intro": esc(raw.get("intro", "")),
            "concerned_nodes": ", ".join(esc(n) for n in concerned_nodes),
        }
        if "reference_table" in raw:
            rt = raw["reference_table"] or {}
            columns = [esc(c) for c in rt.get("columns", [])]
            rows = [[esc(cell) for cell in row] for row in rt.get("rows", [])]
            brique["kind"] = "reference_table"
            brique["table"] = {"columns": columns, "rows": rows}
            brique["col_spec"] = "|".join(["p{%.1fcm}" % (16.0 / max(len(columns), 1))] * len(columns))
        else:
            brique["kind"] = "operations"
            brique["operations"] = [_escape_operation(op, warnings) for op in raw.get("operations", []) or []]
        briques.append(brique)

    # --- Plan de maintenance : synthèse de toutes les opérations qui
    #     portent un bloc "attributes" (peu importe la brique) --- une
    #     opération sans "attributes" n'y figure simplement pas. ---
    maintenance_entries = []
    for brique in briques:
        if brique["kind"] != "operations":
            continue
        for op in brique["operations"]:
            if op["attributes"]:
                maintenance_entries.append({"brique": brique["name"], "operation": op["title"], **op["attributes"]})

    return briques, maintenance_entries


def build_nodes_by_component(client_config):
    nodes_by_component = {}
    for n in client_config.get("nodes", []) or []:
        if not isinstance(n, dict):
            continue
        for c in (n.get("components") or []):
            nodes_by_component.setdefault(c, []).append(n.get("id", ""))
    return nodes_by_component


DEFAULT_DEX_TITLE = "Exploitation quotidienne d'une infrastructure Carbonio"


def assemble_document(outdir: Path, client_path: Path = None):
    env = make_env()
    client_mode = client_path is not None
    ce_restrictions = load_yaml(CARBONIO_EDITIONS_PATH).get("restrictions", {})

    if client_mode:
        client_config = load_yaml(client_path)
        # Réutilise directement le contexte du DAT (logos, contacts,
        # adresses déjà échappées, révisions, rédacteur/vérificateur,
        # confidentialité...) --- rédacteur, vérificateur, révisions et
        # confidentialité sont communs aux deux documents et vivent
        # UNIQUEMENT dans le fichier de config client, jamais dans un
        # second fichier propre au DEX (qui n'existe plus).
        dat_ctx = generate_dat.build_context(client_config, client_path.name, outdir=outdir, config_dir=client_path.parent)
        stakeholder_client = dat_ctx["stakeholder_client"]
        stakeholder_integrator = dat_ctx["stakeholder_integrator"]
        services_enabled = client_config.get("services", {}) or {}
        nodes_by_component = build_nodes_by_component(client_config)
        revisions = dat_ctx["revisions"]
        redaction = dat_ctx["client"].get("author", "")
        verification = dat_ctx["client"].get("verificateur", "")
        confidentiality = dat_ctx.get("confidentiality") or "client"
        carbonio_edition = (client_config.get("product", {}) or {}).get("edition", "advanced")
    else:
        # Mode générique (pas de client) : aucun fichier de config à
        # interroger --- valeurs de repli explicites, dans le même esprit
        # que les placeholders "[à préciser]" déjà utilisés côté DAT
        # lorsqu'une information n'est pas fournie.
        outdir.mkdir(parents=True, exist_ok=True)
        logo_file = generate_dat._prepare_logo(generate_dat.DEFAULT_INTEGRATOR_LOGO, outdir, "integrator_logo")
        stakeholder_client = {"name": "", "long_name": "", "logo_file": None}
        stakeholder_integrator = {"name": "Zextras Services", "long_name": "Zextras Services", "logo_file": logo_file}
        services_enabled = {}
        nodes_by_component = {}
        revisions = [
            {"version": "0.1", "date": "[date]", "author": "[auteur]", "note": "Création initiale"},
        ]
        redaction = "[à préciser]"
        verification = "[à préciser]"
        confidentiality = "public"
        carbonio_edition = "advanced"

    warnings = []
    briques, maintenance_entries = build_briques_context(services_enabled, nodes_by_component, client_mode, carbonio_edition, ce_restrictions, warnings)

    latest = revisions[-1] if revisions else {"version": "", "date": ""}
    meta = {
        "title": esc(DEFAULT_DEX_TITLE),
        "redaction": esc(redaction) if not client_mode else redaction,  # déjà échappé côté DAT en mode client
        "verification": esc(verification) if not client_mode else verification,
        "confidentiality": confidentiality,
        "confidentiality_label": CONFIDENTIALITY_LABELS.get(confidentiality, "Public"),
        "current_version": latest.get("version", ""),
        "current_date": latest.get("date", ""),
    }

    ctx = {
        "meta": meta,
        "client_mode": client_mode,
        "confidentiality": confidentiality,
        "client": {"name": esc(DEFAULT_DEX_TITLE), "author": meta["redaction"]},
        "stakeholder_client": stakeholder_client,
        "stakeholder_integrator": stakeholder_integrator,
        "revisions": revisions,
        "generation_date": datetime.date.today().strftime("%d/%m/%Y"),
    }

    preamble = env.get_template("preamble.tex.j2").render(**ctx)
    cover = env.get_template("cover.tex.j2").render(**ctx)
    revisions_chapter = env.get_template("revisions.tex.j2").render(**ctx)
    info_document = env.get_template("info_document.tex.j2").render(**ctx)

    operation_tmpl = env.get_template("operation.tex.j2")
    reference_table_tmpl = env.get_template("reference_table.tex.j2")

    # Le pied de page (date de génération + pagination) n'est activé qu'à
    # partir du chapitre "Introduction et cadrage" (même principe que le
    # DAT) : la page de garde, l'historique des révisions et le sommaire
    # n'en ont pas.
    footer_activation = (
        r"\renewcommand{\footrulewidth}{0.4pt}"
        "\n" r"\fancyfoot[L]{\small\color{graytxt}Document du " + ctx["generation_date"] + "}"
        "\n" r"\fancyfoot[R]{\small\color{graytxt}Page \thepage\ / \pageref{LastPage}}"
    )

    body_parts = [cover, revisions_chapter, footer_activation + "\n\n" + info_document]

    if client_mode:
        stakeholders = env.get_template("stakeholders.tex.j2").render(**ctx)
        body_parts.append(stakeholders)

    if maintenance_entries:
        maintenance_summary = env.get_template("maintenance_summary.tex.j2").render(entries=maintenance_entries, **ctx)
        body_parts.append(maintenance_summary)

    for brique in briques:
        chapter = [f"\\chapter{{{brique['name']}}}"]
        if brique["intro"]:
            chapter.append(brique["intro"])
        if brique["concerned_nodes"]:
            chapter.append(f"\\textbf{{Nœuds concernés~:}} \\texttt{{{brique['concerned_nodes']}}}")
        if brique["kind"] == "reference_table":
            chapter.append(reference_table_tmpl.render(table=brique["table"], col_spec=brique["col_spec"]))
        else:
            for op in brique["operations"]:
                chapter.append(operation_tmpl.render(op=op))
        body_parts.append("\n\n".join(chapter))

    body = "\n\n".join(body_parts)
    doc = preamble + "\n\n\\begin{document}\n\n" + body + "\n\n\\end{document}\n"

    for w in warnings:
        print(w, file=sys.stderr)

    return doc


def main():
    parser = argparse.ArgumentParser(description="Génère un Document d'Exploitation (DEX) Carbonio.")
    parser.add_argument("--client", default=None, help="Fichier de config client (YAML, format DAT) pour un DEX personnalisé")
    parser.add_argument(
        "--outdir", default=None,
        help="Répertoire de sortie. Mode générique : défaut build/dex (visible, suivi par git). "
             "Mode --client : défaut build/customers/<nom_court_client>/ (même dossier que le DAT de ce client, non suivi par git)."
    )
    parser.add_argument("--compile", action="store_true", help="Compiler le .tex en PDF via xelatex")
    parser.add_argument("--name", default=None, help="Nom de base du fichier généré")
    args = parser.parse_args()

    client_path = Path(args.client) if args.client else None
    default_name = "DEX_Carbonio" if not client_path else f"DEX_{client_path.stem}"

    if client_path:
        # Même dossier client que le DAT (build/customers/<nom_court>/),
        # avec le même sous-dossier "generation" pour les fichiers
        # intermédiaires --- le PDF final est copié à la racine du dossier
        # client, aux côtés du DAT s'il a déjà été généré.
        client_config = load_yaml(client_path)
        outdir_base = BASE_DIR / (args.outdir or "build/customers")
        client_dir = outdir_base / client_config["client"]["name"].replace(" ", "_")
        generation_dir = client_dir / "generation"
    else:
        # Mode générique : dossier plat, visible et suivi par git (c'est
        # l'exemple de référence, pas un document client).
        generation_dir = BASE_DIR / (args.outdir or "build/dex")
        client_dir = generation_dir

    generation_dir.mkdir(parents=True, exist_ok=True)

    doc = assemble_document(generation_dir, client_path)

    base_name = args.name or default_name
    tex_path = generation_dir / f"{base_name}.tex"
    tex_path.write_text(doc, encoding="utf-8")
    print(f"[OK] Document LaTeX généré : {tex_path}")

    if args.compile:
        ok, result = generate_dat.compile_pdf(tex_path, generation_dir)
        if ok:
            final_pdf = client_dir / f"{base_name}.pdf"
            if final_pdf != tex_path.with_suffix(".pdf"):
                import shutil
                shutil.copyfile(tex_path.with_suffix(".pdf"), final_pdf)
            print(f"[OK] PDF généré : {final_pdf}")
        else:
            print("[ERREUR] Échec de la compilation LaTeX.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
