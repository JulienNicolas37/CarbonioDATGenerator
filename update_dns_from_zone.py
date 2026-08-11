#!/usr/bin/env python3
"""
Met à jour les enregistrements MX, SPF et DMARC d'un fichier de
configuration client directement depuis les zones DNS réelles.

Ne touche JAMAIS au DKIM : le sélecteur reste une information saisie à la
main (il n'est pas "découvrable" en DNS sans le connaître déjà), et la
validité du contenu de l'enregistrement DNS DKIM est de la responsabilité
de l'AS/AV et des outils de monitoring --- pas de ce générateur.

Le fichier est réécrit EN PLACE avec `ruamel.yaml`, qui préserve les
commentaires et la mise en forme existante (contrairement à `pyyaml`, qui
les perdrait au moment de la réécriture).

En cas d'échec de résolution pour un domaine (DNS indisponible, NXDOMAIN,
aucun enregistrement trouvé...), la valeur déjà présente dans le fichier
est CONSERVÉE --- rien n'est jamais écrasé sur un problème réseau passager.
Le fichier n'est réécrit que s'il y a au moins un changement réel.

Usage :
    python3 update_dns_from_zone.py config/client.yaml
    python3 update_dns_from_zone.py config/client.yaml --dry-run
"""
import argparse
import sys
from pathlib import Path

try:
    import dns.resolver
except ImportError:
    print("Le paquet 'dnspython' est requis : pip install dnspython --break-system-packages", file=sys.stderr)
    sys.exit(1)

try:
    from ruamel.yaml import YAML
except ImportError:
    print("Le paquet 'ruamel.yaml' est requis : pip install ruamel.yaml --break-system-packages", file=sys.stderr)
    sys.exit(1)


def _resolve_mx(domain):
    """Retourne (liste de {priority, hostname} triée par priorité, erreur).
    Gère le cas particulier du "MX nul" (RFC 7505, exchange = ".") qui
    signifie explicitement "ce domaine n'accepte aucun e-mail" --- le
    hostname est alors représenté par "." plutôt que par une chaîne vide,
    qui serait trompeuse dans le DAT.

    Chaque enregistrement est construit en style "flow" ({priority: ...,
    hostname: ...}) pour rester cohérent avec le style compact déjà
    utilisé dans les fichiers de configuration --- évite de faire basculer
    tout le bloc en style développé au moindre changement, ce qui
    polluerait inutilement un `git diff`."""
    from ruamel.yaml.comments import CommentedMap

    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=10)
        entries = sorted(
            ((int(r.preference), str(r.exchange).rstrip(".") or ".") for r in answers),
            key=lambda t: t[0],
        )
        records = []
        for priority, hostname in entries:
            m = CommentedMap([("priority", priority), ("hostname", hostname)])
            m.fa.set_flow_style()
            records.append(m)
        return records, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _resolve_txt(name):
    """Retourne (liste de chaînes TXT concaténées, erreur)."""
    try:
        answers = dns.resolver.resolve(name, "TXT", lifetime=10)
        values = ["".join(part.decode("utf-8", errors="replace") for part in r.strings) for r in answers]
        return values, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _resolve_spf(domain):
    values, err = _resolve_txt(domain)
    if err:
        return None, err
    spf_values = [v for v in values if v.lower().startswith("v=spf1")]
    if not spf_values:
        return None, "aucun enregistrement TXT commençant par v=spf1"
    return spf_values[0], None


def _resolve_dmarc(domain):
    values, err = _resolve_txt(f"_dmarc.{domain}")
    if err:
        return None, err
    dmarc_values = [v for v in values if v.lower().startswith("v=dmarc1")]
    if not dmarc_values:
        return None, "aucun enregistrement TXT commençant par v=DMARC1"
    return dmarc_values[0], None


def update_dns_from_zone(config_path: Path, dry_run: bool = False):
    """Met à jour en place (préservant commentaires/mise en forme) les
    champs mx_records/spf/dmarc de chaque domaine déclaré dans
    dns.domains, à partir d'une résolution DNS réelle."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # évite le retour à la ligne automatique des longues valeurs (SPF/DMARC)

    with open(config_path, encoding="utf-8") as f:
        data = yaml.load(f)

    domains = ((data.get("dns") or {}).get("domains")) or []
    if not domains:
        print("Aucun domaine déclaré dans dns.domains --- rien à faire.")
        return

    changes = []
    errors = []
    checks_attempted = 0

    for d in domains:
        domain_name = d.get("domain")
        if not domain_name:
            continue

        mx_records, mx_err = _resolve_mx(domain_name)
        checks_attempted += 1
        if mx_err:
            errors.append(f"{domain_name} [MX] : {mx_err}")
        elif list(d.get("mx_records") or []) != mx_records:
            d["mx_records"] = mx_records
            changes.append(f"{domain_name} [MX] mis à jour ({len(mx_records)} enregistrement(s))")

        spf, spf_err = _resolve_spf(domain_name)
        checks_attempted += 1
        if spf_err:
            errors.append(f"{domain_name} [SPF] : {spf_err}")
        elif d.get("spf") != spf:
            d["spf"] = spf
            changes.append(f"{domain_name} [SPF] mis à jour")

        dmarc, dmarc_err = _resolve_dmarc(domain_name)
        checks_attempted += 1
        if dmarc_err:
            errors.append(f"{domain_name} [DMARC] : {dmarc_err}")
        elif d.get("dmarc") != dmarc:
            d["dmarc"] = dmarc
            changes.append(f"{domain_name} [DMARC] mis à jour")

    print(f"--- Mise à jour DNS pour {config_path} ---")
    if changes:
        for c in changes:
            print(f"[OK] {c}")
    elif checks_attempted > 0 and len(errors) == checks_attempted:
        # Toutes les résolutions ont échoué, pour tous les domaines (ex.
        # aucune connexion réseau) --- à ne pas confondre avec "tout
        # correspond déjà au DNS réel", qui suppose d'avoir pu vérifier.
        print("Aucune mise à jour effectuée : toutes les résolutions DNS ont échoué "
              "(voir le détail ci-dessous). Fichier non modifié.")
    else:
        print("Aucun changement détecté (les valeurs en config correspondent déjà au DNS réel).")

    if errors:
        print("\nÉchecs de résolution (valeurs existantes conservées, rien n'est écrasé) :")
        for e in errors:
            print(f"[ATTENTION] {e}")

    if dry_run:
        print("\n(mode --dry-run : fichier non modifié)")
        return

    if changes:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"\nFichier {config_path} mis à jour.")


def main():
    parser = argparse.ArgumentParser(
        description="Met à jour MX/SPF/DMARC d'un fichier de config client depuis le DNS réel (jamais le DKIM)."
    )
    parser.add_argument("config", help="Chemin vers le fichier de configuration client (YAML)")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les changements sans modifier le fichier")
    args = parser.parse_args()
    update_dns_from_zone(Path(args.config), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
