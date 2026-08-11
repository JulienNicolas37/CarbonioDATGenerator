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


def _escape_operation(op):
    """Échappe les champs texte normaux d'une opération --- PAS les champs
    verbatim (commands/example_output), qui passent par `lstlisting` et
    n'ont donc besoin d'aucun échappement LaTeX."""
    out = dict(op)
    out["title"] = esc(op.get("title", ""))
    out["description"] = esc(op.get("description", ""))
    out["prerequisites"] = esc(op.get("prerequisites", ""))
    out["explanation"] = esc(op.get("explanation", ""))
    out["warning"] = esc(op.get("warning", ""))
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
    return out


def build_briques_context(services_enabled, nodes_by_component, client_mode, carbonio_edition, ce_restrictions):
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
            brique["operations"] = [_escape_operation(op) for op in raw.get("operations", []) or []]
        briques.append(brique)
    return briques


def build_nodes_by_component(client_config):
    nodes_by_component = {}
    for n in client_config.get("nodes", []) or []:
        if not isinstance(n, dict):
            continue
        for c in (n.get("components") or []):
            nodes_by_component.setdefault(c, []).append(n.get("id", ""))
    return nodes_by_component


def assemble_document(meta_config, outdir: Path, client_path: Path = None):
    env = make_env()
    client_mode = client_path is not None
    ce_restrictions = load_yaml(CARBONIO_EDITIONS_PATH).get("restrictions", {})

    if client_mode:
        client_config = load_yaml(client_path)
        # Réutilise directement le contexte du DAT (logos, contacts,
        # adresses déjà échappées, révisions, rédacteur/vérificateur...)
        # plutôt que de dupliquer cette logique --- une seule source de
        # vérité dans le fichier de config client.
        dat_ctx = generate_dat.build_context(client_config, client_path.name, outdir=outdir, config_dir=client_path.parent)
        stakeholder_client = dat_ctx["stakeholder_client"]
        stakeholder_integrator = dat_ctx["stakeholder_integrator"]
        services_enabled = client_config.get("services", {}) or {}
        nodes_by_component = build_nodes_by_component(client_config)
        revisions = dat_ctx["revisions"]
        redaction = dat_ctx["client"].get("author") or meta_config.get("redaction", "")
        verification = dat_ctx["client"].get("verificateur") or meta_config.get("verification", "")
        confidentiality = meta_config.get("confidentiality") or dat_ctx.get("confidentiality") or "client"
        carbonio_edition = (client_config.get("client", {}) or {}).get("carbonio_edition", "advanced")
    else:
        outdir.mkdir(parents=True, exist_ok=True)
        logo_file = generate_dat._prepare_logo(generate_dat.DEFAULT_INTEGRATOR_LOGO, outdir, "integrator_logo")
        stakeholder_client = {"name": "", "long_name": "", "logo_file": None}
        stakeholder_integrator = {"name": "Zextras Services", "long_name": "Zextras Services", "logo_file": logo_file}
        services_enabled = {}
        nodes_by_component = {}
        revisions = [
            {"version": esc(r.get("version", "")), "date": esc(r.get("date", "")),
             "author": esc(r.get("author", "")), "note": esc(r.get("note", ""))}
            for r in meta_config.get("revisions", []) or []
            if isinstance(r, dict)
        ]
        redaction = meta_config.get("redaction", "")
        verification = meta_config.get("verification", "")
        confidentiality = meta_config.get("confidentiality") or "public"
        carbonio_edition = "advanced"

    briques = build_briques_context(services_enabled, nodes_by_component, client_mode, carbonio_edition, ce_restrictions)

    latest = revisions[-1] if revisions else {"version": "", "date": ""}
    meta = {
        "title": esc(meta_config.get("title", "Document d'Exploitation")),
        "redaction": esc(redaction) if not client_mode else redaction,  # déjà échappé côté DAT en mode client
        "verification": esc(verification) if not client_mode else verification,
        "confidentiality": confidentiality,
        "confidentiality_label": CONFIDENTIALITY_LABELS.get(confidentiality, "Public"),
        "current_version": latest["version"],
        "current_date": latest["date"],
    }

    ctx = {
        "meta": meta,
        "client_mode": client_mode,
        "confidentiality": confidentiality,
        "client": {"name": esc(meta_config.get("title", "Document d'Exploitation")), "author": meta["redaction"]},
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
    return doc


def main():
    parser = argparse.ArgumentParser(description="Génère un Document d'Exploitation (DEX) Carbonio.")
    parser.add_argument("--meta", default=str(BASE_DIR / "config" / "dex_meta.yaml"), help="Fichier de métadonnées du document")
    parser.add_argument("--client", default=None, help="Fichier de config client (YAML, format DAT) pour un DEX personnalisé")
    parser.add_argument("--outdir", default="build/dex", help="Répertoire de sortie (défaut: build/dex)")
    parser.add_argument("--compile", action="store_true", help="Compiler le .tex en PDF via xelatex")
    parser.add_argument("--name", default=None, help="Nom de base du fichier généré")
    args = parser.parse_args()

    meta_config = load_yaml(Path(args.meta))
    outdir = BASE_DIR / args.outdir
    client_path = Path(args.client) if args.client else None

    doc = assemble_document(meta_config, outdir, client_path)

    default_name = "DEX_Carbonio" if not client_path else f"DEX_{client_path.stem}"
    tex_path = outdir / f"{args.name or default_name}.tex"
    outdir.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(doc, encoding="utf-8")
    print(f"[OK] Document LaTeX généré : {tex_path}")

    if args.compile:
        ok, result = generate_dat.compile_pdf(tex_path, outdir)
        if ok:
            print(f"[OK] PDF généré : {tex_path.with_suffix('.pdf')}")
        else:
            print("[ERREUR] Échec de la compilation LaTeX.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
