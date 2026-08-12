# Générateur de DAT Carbonio

Génère un Document d'Architecture Technique (DAT) LaTeX/PDF pour une
plateforme Zextras Carbonio, à partir d'un fichier de configuration client
(YAML) et de templates modulaires (Jinja2 + LaTeX).

## Installation

Dépendances Python :

```bash
pip install pyyaml jinja2 --break-system-packages   # si nécessaire

# Optionnel --- uniquement pour --update-dns / update_dns_from_zone.py
pip install dnspython ruamel.yaml --break-system-packages
```

Dépendances système : une distribution LaTeX (TeX Live) avec `xelatex`
(nécessaire pour la police Open Sans via `fontspec` --- ce générateur ne
fonctionne plus avec `pdflatex`), et les paquets `babel` (langue
française), `tikz`, `adjustbox`, `longtable`, `colortbl`, `titlesec`,
`fancyhdr`, `lastpage`, `multirow`, `pdflscape`, `fontspec`. La police
**Open Sans** doit être installée comme police système (pas comme paquet
LaTeX). Sur Debian/Ubuntu :

```bash
sudo apt-get install texlive-xetex texlive-latex-recommended \
                      texlive-latex-extra texlive-lang-french \
                      texlive-pictures fonts-open-sans
# texlive-latex-extra fournit adjustbox (redimensionnement automatique des schémas)
# fonts-open-sans fournit la police Open Sans (détectée via fontconfig/fc-list)
```

## Mise à jour MX/SPF/DMARC depuis le DNS réel (optionnel)

`update_dns_from_zone.py` interroge le DNS réel de chaque domaine listé
dans `dns.domains` et met à jour les champs `mx_records`/`spf`/`dmarc`
directement dans le fichier de configuration client --- **jamais le
DKIM** (le sélecteur reste saisi à la main ; la validité du contenu de
l'enregistrement DNS DKIM relève de l'AS/AV et des outils de monitoring,
pas de ce générateur).

```bash
# En 2 étapes (le script reste utilisable seul, y compris en CI/CRON)
python3 update_dns_from_zone.py config/client.yaml
python3 generate_dat.py config/client.yaml --compile

# En 1 étape
python3 generate_dat.py config/client.yaml --update-dns --compile

# Sans rien modifier (affiche les écarts détectés sans toucher au fichier)
python3 update_dns_from_zone.py config/client.yaml --dry-run
```

**Principes de sécurité du script** :
- Le fichier est réécrit via `ruamel.yaml`, qui préserve les commentaires
  et la mise en forme existante --- pas via `pyyaml`, qui les
  supprimerait.
- Si la résolution échoue pour un domaine (DNS indisponible, NXDOMAIN,
  aucun enregistrement trouvé...), **la valeur déjà présente dans le
  fichier est conservée** --- rien n'est jamais écrasé sur un problème
  réseau passager. Un résumé des échecs est affiché.
- Le fichier n'est réécrit que s'il y a au moins un changement réel
  (exécution idempotente).
- Un domaine sans MX qui déclare explicitement "aucun e-mail accepté"
  (MX nul, RFC 7505) est représenté fidèlement (`hostname: "."`) plutôt
  que par un champ vide trompeur.

**Pourquoi cette mise à jour ne se fait jamais automatiquement à chaque
génération** (voir aussi le fichier `CLAUDE.md`, section sur le moteur de
flux) : ce générateur vise un document **déterministe et reproductible**
--- la même config doit toujours produire le même PDF. Aller chercher le
DNS en direct à chaque compilation casserait cette propriété et pourrait
même documenter la mauvaise information (ex. le DAT décrit une
architecture cible dont le DNS n'a pas encore basculé). D'où le choix
d'une étape explicite et séparée qui **réécrit la config** (source de
vérité versionnée), plutôt qu'une résolution "à la volée" au moment de la
génération.

## Document d'Exploitation (DEX) --- second générateur du dépôt

`generate_dex.py` produit un Document d'Exploitation (procédures
d'administration Carbonio). Même modèle architectural que le DAT --- même
préambule partagé (`templates/preamble.tex.j2` : police, couleurs,
en-tête/pied de page, logos), même style de page de garde --- avec un
principe supplémentaire : **aucune brique ni opération n'est codée en
dur**.

**Deux modes de génération** :

```bash
# Mode générique --- toutes les briques, aucun nœud listé, pas de parties
# prenantes, classification "Public" par défaut. Document de référence
# valable pour n'importe quelle infrastructure Carbonio.
python3 generate_dex.py --compile

# Mode client --- ne garde que les briques dont au moins un service listé
# est activé chez ce client, liste les nœuds concernés par chapitre,
# ajoute les parties prenantes (réutilisées du DAT) et un paragraphe de
# propriété intellectuelle, classification "Client" par défaut.
python3 generate_dex.py --client config/univ_amboise.yaml --compile
```

### Ajouter du contenu sans toucher au code

Chaque chapitre ("brique") est un fichier YAML dans `briques/*.yaml`,
chargé automatiquement au démarrage (ordre = ordre alphabétique des noms
de fichiers --- préfixe numérique conseillé : `00_`, `10_`, `20_`...).
**Ajouter une brique = déposer un fichier. Ajouter une opération à une
brique existante = ajouter une entrée dans son fichier.** Dans les deux
cas, zéro ligne de code à modifier.

Deux "squelettes" génériques disponibles :

```yaml
# Squelette "operations" --- le plus courant
brique: "Nom du chapitre"
intro: "Texte d'introduction (optionnel)"
services: ["chat", "files"]         # optionnel --- brique masquée en mode
                                     # --client si aucun de ces services
                                     # n'est activé. Absent = universelle,
                                     # toujours incluse (ex. gestion des
                                     # comptes, certificats SSL...).
components: ["proxy", "mta_auth"]   # optionnel --- affiche "Nœuds
                                     # concernés" en mode --client (résolu
                                     # dynamiquement depuis la topologie du
                                     # client). Sans effet en mode générique.
ce_feature: "backup"                # optionnel --- clé de
                                     # templates/carbonio_editions.yaml.
                                     # Si le client est en Community
                                     # Edition ET que cette fonctionnalité
                                     # y est indisponible, la brique est
                                     # masquée en mode --client.
operations:
  - title: "Titre de l'opération"
    description: "..."               # optionnel
    prerequisites: "..."              # optionnel --- encadré avant les commandes
    items: ["...", "..."]             # optionnel --- liste à puces
    commands: ["...", "..."]          # optionnel --- bloc de commande(s)
    explanation: "..."                # optionnel --- texte après les commandes
    example_output: "..."             # optionnel --- bloc de sortie de commande
    options_table: [{option: "...", description: "..."}]  # optionnel
    warning: "..."                    # optionnel --- encadré rouge final

# Squelette "reference_table" --- table de référence simple (ex. logs)
brique: "Nom du chapitre"
reference_table:
  columns: ["Col1", "Col2"]
  rows: [["v1", "v2"], ["v3", "v4"]]
```

Les champs `commands`/`example_output` sont insérés tels quels (style
`lstlisting`) --- aucun échappement LaTeX nécessaire, sûr pour des
commandes shell contenant `_`, `%`, `$`, `{`, `}`... Tous les autres champs
texte sont échappés automatiquement.

### Métadonnées du document : communes avec le DAT, aucun fichier propre au DEX

Rédacteur (`client.author`), vérificateur (`client.verificateur`),
historique des révisions (`revisions:`) et classification
(`client.classification`) sont **exclusivement** lus depuis le fichier de
config client --- exactement les mêmes champs que ceux utilisés par le
DAT (voir plus haut). Il n'existe **aucun fichier de configuration propre
au DEX** : rien à maintenir en double entre les deux documents.

En mode générique (sans `--client`, aucun fichier à interroger), ces
informations retombent sur des valeurs de repli explicites
(`[à préciser]`, dans le même esprit que les autres placeholders du DAT).

### Ce qui manque volontairement pour l'instant

Réindexation des comptes et génération de la GAL --- à ajouter dans une
prochaine version (voir `CHANGELOG.md`).

## Community Edition vs Advanced (`templates/carbonio_editions.yaml`)

Catalogue **volontairement conservateur** des fonctionnalités confirmées
absentes de Carbonio Community Edition (CE) --- uniquement celles
vérifiées auprès de sources officielles Zextras (voir `CLAUDE.md` pour le
détail) : sauvegarde native (Carbonio Backup), HSM, legal hold, gestion
des terminaux mobiles (MDM), personnalisation de marque (white-labeling).
**À étendre par Julien** avec le tableau de comparaison officiel Zextras
si une couverture plus large est nécessaire.

Deux champs sur `client:` pilotent ce mécanisme (voir plus haut) :
`carbonio_edition` (voir plus haut) --- le numéro de version affiché
reste `product.version`, quelle que soit l'édition. Effets concrets :
- **DAT** : affichage de l'édition dans "Solution Zextras Carbonio" ;
  alerte si une fonctionnalité incompatible est configurée malgré tout
  (ex. HSM activé sur un mailstore alors que le client est en CE).
- **DEX (mode `--client`)** : une brique portant `ce_feature: "backup"`
  (ou toute autre clé du catalogue) disparaît automatiquement si cette
  fonctionnalité est indisponible dans l'édition du client --- sans
  qu'il soit nécessaire de désactiver la brique à la main.

## Versionnement

Ce projet suit un numéro de version simple, stocké dans le fichier
`VERSION` (ex. `1.0.0`), et documenté dans `CHANGELOG.md`. Chaque archive
livrée porte ce numéro dans son nom (`dat-generator-v1.0.0.zip`) pour
pouvoir suivre les évolutions dans le temps.

## Utilisation

```bash
# Génère uniquement le .tex (pas de compilation)
python3 generate_dat.py config/client_exemple.yaml

# Génère le .tex ET compile le PDF
python3 generate_dat.py config/client_exemple.yaml --compile

# Choisir le dossier racine de sortie et le nom du fichier
python3 generate_dat.py config/univ_amboise.yaml --outdir build --name DAT_UnivAmboise --compile
```

### Structure des dossiers de sortie

Chaque client a son propre dossier, nommé sur son nom court
(`client.name`, espaces remplacés par des underscores) :

```
<outdir>/<Nom_Court_Client>/
├── DAT_<...>.pdf              # PDF final --- seul fichier suivi par git
├── DEX_<...>.pdf              # idem pour le DEX de ce même client (--client)
└── generation/                # fichiers intermédiaires --- jamais suivis par git
    ├── DAT_<...>.tex
    ├── DAT_<...>.aux/.log/.out/.toc
    ├── client_logo.png / integrator_logo.png
    └── ...
```

Le DAT et le DEX d'un même client (`generate_dex.py --client
config/univ_amboise.yaml`) partagent le **même** dossier client et le
même sous-dossier `generation/` --- les deux documents d'un client sont
ainsi toujours au même endroit.

**Par défaut** (`--outdir` non précisé), les documents client vont dans
`build/customers/` (`.gitignore` --- jamais suivi par git, y compris le
sous-dossier `generation/` et les résidus LaTeX `.aux`/`.log`/`.out`/`.toc`
où qu'ils se trouvent). Pour les **deux exemples fournis**
(`config/client_exemple*.yaml`), utiliser explicitement `--outdir build`
--- ce dossier reste suivi par git (seuls les PDF finaux, pas les fichiers
de `generation/`), pour que les exemples de sortie restent toujours
visibles dans le dépôt.

Le mode générique du DEX (`generate_dex.py --compile`, sans `--client`)
n'est pas concerné par cette structure par dossier client --- il reste
plat dans `build/dex/` (visible et suivi par git), puisqu'il ne documente
aucun client en particulier.

### Deux fichiers d'exemple fournis

- `config/client_exemple.yaml` --- petite infrastructure (1 nœud par rôle,
  hors mailstores).
- `config/client_exemple_grande_infra.yaml` --- infrastructure "éclatée" en
  haute disponibilité (2 Proxy, 2 MTA IN, 2 MTA OUT, 2 MTA AUTH, 3
  Mailstores, 2 nœuds Application, 3 nœuds Services) --- utile comme base
  de départ pour une infrastructure de taille réelle, et comme test de
  charge du générateur (grille multi-rangées, nombreux flux colorés).

## Créer un DAT pour un nouveau client

1. Copier l'exemple le plus proche de la taille réelle du client
   (`config/client_exemple.yaml` ou `config/client_exemple_grande_infra.yaml`)
   vers `config/<nom_client>.yaml`.
2. Adapter les sections `client`, `sla`, `services`, `zones`, `nodes`,
   `flows` à la plateforme réelle du client (voir "Structure du fichier de
   configuration" ci-dessous).
3. Lancer `python3 generate_dat.py config/<nom_client>.yaml --compile`.
4. Relire le PDF généré et compléter les passages signalés en
   **rouge italique entre crochets** (`[à compléter]`), qui correspondent
   aux informations que le fichier de configuration ne fournit pas encore.

## Logos et identité (en-tête, pied de page, chapitre "Parties prenantes")

- Le **logo du client** doit être placé dans le même dossier que son
  fichier de configuration, puis référencé via `client.logo:` (chemin
  relatif à ce fichier). En son absence, l'en-tête affiche le nom du client
  en texte à la place.
- Le **logo Zextras Services** est fourni avec le programme
  (`templates/assets/logo_zextras_services.png`) et utilisé par défaut pour
  `integrator.logo` --- à ne renseigner que si un autre intégrateur
  intervient sur cette plateforme.
- Les deux logos apparaissent en en-tête sur toutes les pages (sauf la
  première page de chaque chapitre, qui suit la convention LaTeX standard
  `\pagestyle{plain}` --- comportement normal des classes `report`/`book`,
  pas un bug).
- Le pied de page reprend le nom et le site web de l'intégrateur, ainsi que
  la pagination.
- Le chapitre "Parties prenantes" (juste après l'introduction) détaille
  nom long, description, site web, adresse et contacts (avec rôle libre)
  pour le client ET pour l'intégrateur.

## Structure du fichier de configuration

```yaml
client:
  name: "..."            # page de garde, en-tête
  scope: "..."           # page de garde
  author: "..."           # Rédacteur (couverture, repris par le DEX en mode --client)
  verificateur: "..."     # Vérificateur (couverture, repris par le DEX en mode --client)
  version: "1.0"
  date: "JJ/MM/AAAA"
  classification: "Confidentiel"  # normalisé en Public/Client/Restreint/Confidentiel
                                   # pour la table de confidentialité du chapitre 1 ---
                                   # "Confidentiel" par défaut si la valeur ne correspond
                                   # à aucune des 4 options
  carbonio_edition: "advanced"    # "ce" | "advanced" --- "advanced" si absent. Si "ce",
                                   # les fonctionnalités absentes de la Community Edition
                                   # (voir templates/carbonio_editions.yaml) déclenchent des
                                   # alertes de cohérence (ex. HSM) et masquent certaines
                                   # briques du DEX (ex. sauvegarde native). Le numéro de
                                   # version reste porté par product.version (plus bas) ---
                                   # pas de second champ de version dédié à la CE.
  long_name: "..."                       # nouveau : chapitre "Parties prenantes"
  logo: "logo_client.png"                # nouveau : chemin relatif à CE fichier de config
  description: "..."                     # nouveau
  website: "https://www.client.fr"       # nouveau
  address: ["12 rue Exemple", "75000 Paris"]  # nouveau
  emergency_phone: "..."                 # nouveau
  contacts:                              # nouveau --- rôle libre
    - {name: "Jean Dupont", role: "Responsable de projet", email: "...", phone: "..."}
    - {name: "Marie Martin", role: "Responsable technique", email: "...", phone: "..."}

# Intégrateur (Zextras Services par défaut) --- même structure que "client",
# sans "scope"/"version"/"date"/"classification". Le logo par défaut
# (templates/assets/logo_zextras_services.png) est utilisé si "logo:" est
# absent.
integrator:
  name: "Zextras Services"
  long_name: "Zextras Services"
  description: "..."
  website: "https://www.zextras-services.fr"
  address: ["1 allée Ferdinand de Lesseps", "37200 Tours"]
  contacts:
    - {name: "Julien NICOLAS", role: "Responsable projet", email: "julien.nicolas@zextras.fr", phone: "06 69 40 25 96"}
    - {name: "Laurent FRANÇOISE", role: "Responsable technique", email: "laurent.francoise@zextras.fr"}

# Chapitre "Solution Zextras Carbonio" --- optionnel (valeurs par défaut sinon).
product:
  version: "25.9.0"
  release_date: "30/09/2025"
  version_check_url: "https://docs.zextras.com/en/carbonio-release-notes/latest"
  user_doc_url: "https://docs.zextras.com/en/user-guide"
  admin_doc_url: "https://docs.zextras.com/en/carbonio-admin-guide"

# Informations de licence contractuelle --- affichées dans le même chapitre.
license:
  accounts: 500              # nombre de comptes
  activesync: 150            # nombre d'accès ActiveSync (mobilité)
  chat: true                 # Oui/Non
  two_fa: true
  s3_storage: false
  video: true
  files: true

sla:                      # optionnel (valeurs par défaut sinon)
  availability: "..."
  rto: "..."
  rpo: "..."
  backup_retention: "..."

# Chapitre "DNS, légitimité et réputation" --- organisé PAR DOMAINE (un
# domaine peut avoir plusieurs MX, un seul SPF/DKIM/DMARC en général). Les
# tableaux du DAT fusionnent automatiquement la cellule "Domaine" sur
# toutes les lignes MX d'un même domaine.
dns:
  domains:
    - domain: "client.fr"
      mx_records:
        - {priority: 10, hostname: "mx1.client.fr"}
        - {priority: 20, hostname: "mx2.client.fr"}
      spf: "v=spf1 mx ip4:192.0.2.10 -all"
      dkim_selector: "carbonio"
      dmarc: "v=DMARC1; p=quarantine; rua=mailto:dmarc@client.fr"
    - domain: "filiale-client.fr"    # autant de domaines que nécessaire
      mx_records:
        - {priority: 10, hostname: "mx1.client.fr"}
      spf: "v=spf1 mx ip4:192.0.2.10 -all"
      dkim_selector: "carbonio"
      dmarc: "v=DMARC1; p=quarantine; rua=mailto:dmarc@client.fr"

# Chapitre "Auto-provisionnement" --- section ENTIÈREMENT OMISE du DAT si
# absente ou si enabled: false (contrairement aux autres chapitres, qui
# affichent un texte standard par défaut).
autoprovisioning:
  enabled: true
  node: "services01"                              # nœud exécutant le script
  script_name: "ad-sync.sh"
  ldap_server: {hostname: "ad01.client.local", ip: "10.0.5.10"}
  arguments: "--full-sync --domain client.fr"
  frequency: "Toutes les 15 minutes (cron)"
  sync_accounts: true
  sync_distribution_lists: true
  sync_resources: false
  sync_signatures: true

# Chapitre "Authentification" --- méthodes combinables librement.
authentication:
  methods: [native, external_ldap]   # sous-ensemble de [native, external_ldap, saml2, preauth]
  connection:
    vhost: "webmail.client.fr"        # nom du V-Host
    url: "https://webmail.client.fr"  # URL de connexion affichée dans le DAT
  native:
    password_policy: "12 caractères minimum, renouvellement tous les 180 jours"
    lockout_policy: "5 tentatives échouées --- verrouillage 15 minutes"
  external_ldap:
    fallback_to_native: true         # repli sur l'authentification native si LDAP externe indisponible
    servers:
      - {hostname: "ad01.client.local", ip: "10.0.5.10"}
      - {hostname: "ad02.client.local", ip: "10.0.5.11"}
  saml2:                             # affiché seulement si "saml2" est dans methods
    idp_metadata_url: "https://sso.client.fr/metadata"
  brute_force_protection:            # protection anti brute-force (fail2ban ou équivalent)
    enabled: true
    tool: "fail2ban"
    details: "Bannissement 15 min après 5 échecs en 10 min, sur proxy et mta_auth"

# Anti-spam / anti-virus --- section TOUJOURS affichée dans le chapitre
# "Architecture fonctionnelle" (avec des placeholders si non renseignée).
antispam_antivirus:
  name: "..."                # nom du système anti-spam / anti-virus
  outbound_filtering: true   # filtrage sortant (Oui/Non)
  inbound_filtering: true    # filtrage entrant (Oui/Non)
  quarantine: true           # quarantaine possible (Oui/Non)

# Chapitre "Support" --- optionnel (valeurs par défaut Zextras Services sinon).
support:
  url: "https://support.zextras-services.fr"
  phone: "+33 1 85 76 01 97"
  escalation_name: "M. NICOLAS Julien"
  escalation_phone: "+33 6 69 40 25 96"

# Chapitre "PCA/PRA" --- description standard générique si enabled: false ;
# détails spécifiques si enabled: true.
pra_pca:
  enabled: false
  description: "..."       # utilisé seulement si enabled: true
  rto: "..."
  rpo: "..."
  secondary_site: "..."

# Chapitre "Interfaces et intégrations" --- ENTIÈREMENT OMIS si cette
# liste est vide/absente (le paramétrage reste disponible pour un usage
# futur, sans forcer l'affichage d'exemples génériques).
interfaces:
  - system: "Solution de supervision (Zabbix)"
    integration: "Collecte de métriques et alerting"
    protocol: "Prometheus exporters / SNMP"

# Chapitre "PCA/PRA" --- indicateurs Oui/Non INDÉPENDANTS. Si enabled:
# false, le DAT affiche "Pas de PCA/PRA spécifique" suivi de la procédure
# par défaut (templates/pca_pra_defaults.yaml, à adapter une fois pour
# toutes plutôt que par client).
pca:
  enabled: false
  description: "..."       # utilisé seulement si enabled: true

pra:
  enabled: true
  description: "..."
  rto: "..."
  rpo: "..."
  secondary_site: "..."

# Documents complémentaires listés en Annexes (simple tableau, sans
# sous-section).
annexes:
  - name: "Document d'exploitation"
    filename: "EXPL_Client.pdf"
    description: "Procédures pas à pas d'administration courante."

# Opérations planifiées (crons), tous nœuds confondus --- tableau en fin de
# chapitre "Architecture technique détaillée".
scheduled_operations:
  - node: "mail01"
    operation: "Sauvegarde Carbonio (backup.sh)"
    schedule:
      - {days: "Lundi-Vendredi", times: ["02:00"]}
      - {days: "Samedi", times: ["02:00", "22:00"]}   # plusieurs heures/jour possibles

services:                 # active/désactive les sections du DAT
  mesh: true
  directory_master: true
  directory_replica: true
  database: true
  mailbox: true
  proxy: true
  mta_in: true
  mta_out: true
  mta_auth: true
  files: true
  docs: true
  chat: true
  videoconf: true
  tasks: true
  monitoring: true

# Équipements réseau représentés en chaîne au-dessus des zones applicatives
# (optionnel). Pour qu'un flux les traverse, référencer leur id dans
# "flows" comme n'importe quel nœud.
network_equipment:
  - id: internet
    label: "Internet"
    type: internet          # internet (ellipse) | router | firewall | switch (rectangle)
  - id: router01
    label: "Routeur"
    type: router
  - id: firewall01
    label: "Pare-feu"
    type: firewall

zones:                    # ordre d'affichage du schéma, haut -> bas
  - id: DMZ
    label: "Zone Publique (DMZ)"
    short_label: "Publique (DMZ)"   # libellé compact affiché DANS le schéma
    max_cols: 2                     # nb de nœuds par rangée avant repli en grille (défaut 3)
  - id: LAN
    label: "Zone Privée (LAN)"
    short_label: "Privée (LAN)"
    max_cols: 3

nodes:
  - id: proxy01
    zone: DMZ                      # doit exister dans "zones"
    hostname: "proxy01.client.fr"
    ip: "192.0.2.10"
    components: [proxy]            # ids du catalogue --- voir liste ci-dessous
    sizing: {vcpu: 4, ram_gb: 8, storage_gb: 50, os: "Rocky Linux 9"}   # optionnel

  - id: mail01                     # mailstore --- champ "mailstore" optionnel dédié
    zone: LAN
    hostname: "mailstore01.client.local"
    ip: "10.0.1.10"
    components: [mesh, mailbox]
    sizing: {vcpu: 8, ram_gb: 16, storage_gb: 500, os: "Rocky Linux 9"}
    mailstore:
      backup_retention_days: 30           # rétention de sauvegarde --- PAR mailstore
      hsm_enabled: true                    # si absent/false : la section HSM n'est pas affichée pour ce nœud
      hot_data_retention_days: 90          # rétention des données "chaudes" sur le stockage primaire
      hsm_target: "S3 (bucket client-hsm-cold)"
    backup:                                # section "Système de sauvegarde des nœuds" (§4.3)
      enabled: true
      schedule:
        - {days: "Lundi-Vendredi", times: ["02:00"]}
        - {days: "Samedi", times: ["02:00", "22:00"]}   # plusieurs heures/jour possibles
    # blocked_protocols: ["smtp"]          # optionnel --- blocage TECHNIQUE réel
    #                                       # (pas une simple exclusion visuelle) : retire
    #                                       # le flux de cette catégorie PARTOUT (schémas ET
    #                                       # matrice) pour ce nœud, car il ne se produit pas
    #                                       # réellement (ex. pare-feu local, service désactivé)

  - id: clients                    # nœud "externe" (pas un serveur réel) --- optionnel,
    zone: EXT                      # alternative/complément à network_equipment
    label: "Clients externes\\\\(webmail, mobile)"  # texte LaTeX libre

# --- Flux réseau : DÉDUITS AUTOMATIQUEMENT, pas déclarés ---
# Il n'y a plus de section "flows:" à remplir. Les flux sont dérivés des
# nœuds/composants ci-dessus et du catalogue de relations standard
# (templates/flow_relations.yaml, fourni avec le programme --- pas par
# client) : proxy -> chaque mailstore, chaque nœud consommateur de LDAP ->
# Directory Master, pare-feu -> chaque MTA IN/AUTH/Proxy, etc. La
# réplication LDAP Master/Replica n'est volontairement jamais générée
# (relation hors standard, sans intérêt sur les schémas).
#
# Deux leviers restent configurables PAR CLIENT, à placer en fin de
# fichier :

# 1) Catégories dont le schéma dédié doit apparaître dans le DAT
#    (Oui/Non) --- une catégorie absente d'ici vaut "Oui" par défaut.
protocol_schemas:
  web: true
  smtp: true
  ldap: true
  udp_video: true
  interne: true
  mesh: true          # le mesh forme un maillage complet entre tous les
                       # nœuds qui l'hébergent --- dense par nature, sur
                       # son propre schéma dédié (n'affecte pas les autres)

# 2) Exclusions PUREMENT VISUELLES sur les schémas --- le flux existe
#    réellement et reste dans la matrice exhaustive de fin de document,
#    seul son tracé sur les schémas est masqué (ex. désencombrer un schéma
#    trop dense). Différent de "blocked_protocols" ci-dessus (blocage
#    technique réel, qui retire le flux partout). Appariement des nœuds
#    dans n'importe quel sens.
flow_diagram_exclusions:
  - {node1: "proxy02", node2: "mail03", category: "web"}
```

### Types de composants disponibles pour `nodes[].components`

Chaque nœud peut héberger un ou plusieurs composants, listés sous forme
d'identifiants dans `components: [...]`. Un même id ne peut être activé
dans le DAT que si `services.<id>: true` est également positionné (voir
plus haut). La liste ci-dessous correspond au catalogue actuel
(`templates/components_catalog.yaml`) :

| id (`components:`) | Nom affiché dans le DAT | Rôle |
|---|---|---|
| `mesh` | Mesh | Coordination inter-nœuds / service discovery --- présent sur **tous** les nœuds d'infrastructure |
| `directory_master` | Directory Master (LDAP) | Annuaire LDAP en écriture --- un seul par infrastructure |
| `directory_replica` | Directory Replica (LDAP) | Annuaire LDAP en lecture, synchronisé depuis le Master |
| `database` | Database | Bases PostgreSQL (mailbox, files, docs, tâches, chat) |
| `mailbox` | Mailstore | Cœur applicatif : messages, calendriers, contacts, API SOAP/REST, IMAP/POP3 |
| `proxy` | Proxy | Reverse-proxy HTTP/S et proxy mail, point d'entrée public |
| `mta_in` | MTA IN | Réception du courrier entrant, filtrage antispam/antivirus, vérification SPF/DKIM/DMARC |
| `mta_out` | MTA OUT | Émission du courrier sortant, signature DKIM |
| `mta_auth` | MTA AUTH | Soumission authentifiée (port 587) |
| `files` | Files | Stockage de fichiers et partage documentaire |
| `docs` | Docs (édition collaborative) | Édition bureautique en ligne via Collabora Online (WOPI) |
| `chat` | Chat (Workstream Collaboration) | Messagerie instantanée temps réel, notifications |
| `videoconf` | Visioconférence (Video Server) | Agrégation des flux WebRTC des réunions vidéo --- **zone DMZ** (NAT 1:1 direct) |
| `tasks` | Tasks | Gestion de tâches / listes de choses à faire |
| `monitoring` | Monitoring | Supervision et métriques de la plateforme |

**Note de conception** : il n'existe volontairement pas d'id générique
`mta` ou `directory`. Le MTA est toujours scindé en IN/OUT/AUTH et LDAP en
Master/Replica, même sur une petite infrastructure où plusieurs rôles sont
colocalisés sur les mêmes nœuds (lister simplement plusieurs ids dans
`components:` pour ce nœud). Objectif : rendre visible chaque rôle
réellement en jeu, plutôt que de le masquer dans un composant générique.

**Toutes les informations d'un rôle vivent dans un seul fichier** :
`templates/partials/components/<id>.tex.j2` (ou `_generic.tex.j2` en
repli) contient la description commerciale, le rôle technique, les
paquets, les ports et le tableau des nœuds pour CE rôle --- rien n'est
dispersé ailleurs. Le "MTA (Mail Transfer Agent)" chapitre ci-dessous en
est l'exception volontaire de présentation, pas de contenu : il ajoute un
paragraphe d'introduction générique commun, affiché une seule fois.

### Regroupement de composants (`components_catalog.yaml[id].group`)

Un composant peut porter un champ optionnel `group` (ex. `mta_in`,
`mta_out`, `mta_auth` portent tous `group: "mta"`). Le générateur affiche
alors automatiquement une introduction générique (`templates/
component_groups.yaml[group].intro`) sous forme de `\subsection`, suivie
de chaque composant du groupe en `\subsubsection`, plutôt que de les
lister à plat au même niveau que les autres composants (Mesh, Proxy...).
Pour créer un nouveau regroupement, ajouter une entrée dans
`templates/component_groups.yaml` et référencer son id via `group:` dans
les entrées concernées de `components_catalog.yaml`.

### Description technico-commerciale (`components_catalog.yaml[id].commercial`)

Chaque composant du catalogue porte un champ `commercial` (description
technico-commerciale, orientée décideur) affiché en **introduction de son
propre `\subsection`/`\subsubsection`** dans "Composants Carbonio et
rôles" --- pas dans un chapitre séparé qui les listerait toutes à la suite.

### Services rendus aux utilisateurs (`templates/user_services_catalog.yaml`)

Distinct du catalogue technique : ce catalogue fournit une description
orientée usage final (pas technique, pas commerciale) pour les briques que
l'utilisateur perçoit réellement (Mail, Agenda, Contacts, Fichiers, Édition
collaborative, Chat, Visioconférence, Tâches). Chaque entrée porte un
`trigger` (l'id de `services:` qui la déclenche) --- LDAP/Mesh/Database
n'y figurent volontairement pas, ce sont des briques d'infrastructure
invisibles pour l'utilisateur final.

#### Cas type : nœuds "Services01/02/03" et nœuds "Application" multi-rôles

Pattern observé sur les infrastructures réelles : un pool de nœuds Services
qui partagent tous `mesh`, mais où un seul porte `directory_master`, un ou
plusieurs `directory_replica`, et un (ou le même) `database` :

```yaml
  - id: services01
    zone: LAN
    hostname: "services01.client.local"
    components: [mesh, directory_master]

  - id: services02
    zone: LAN
    hostname: "services02.client.local"
    components: [mesh, directory_replica]

  - id: services03
    zone: LAN
    hostname: "services03.client.local"
    components: [mesh, database]
```

Le DAT généré donne alors à `directory_master` et `directory_replica`
chacun leur propre sous-section, avec un **renvoi croisé automatique**
(« Ce Master réplique vers : services02 » / « Synchronisé depuis :
services01 ») --- pas de champ supplémentaire à saisir, c'est déduit de
`components:`.

De même, un nœud "Application" peut regrouper plusieurs rôles de
collaboration sans règle fixe (Chat+Tasks, ou Files+Docs, ou les deux) :

```yaml
  - id: application01
    zone: LAN
    hostname: "application01.client.local"
    components: [mesh, chat, tasks]

  - id: application02
    zone: LAN
    hostname: "application02.client.local"
    components: [mesh, files, docs]
```

Cette liste de composants évolue avec `templates/components_catalog.yaml` :
voir la section "Ajouter un nouveau composant Carbonio" plus bas.

### Catégories de flux et couleurs

Chaque flux dérivé automatiquement (voir "Flux réseau : dérivés
automatiquement" plus haut) porte une `category` qui déclenche :
- une couleur cohérente sur le schéma (et la fusion visuelle des flux
  parallèles de même catégorie entre les deux mêmes nœuds) ;
- une entrée dans la légende sous le schéma ;
- une ligne dans la table de référence "Légende des catégories de flux" du
  DAT (uniquement les catégories effectivement utilisées par ce client).

Catalogue par défaut (`templates/flow_categories.yaml`), avec sa couleur :

| `category` | Libellé | Couleur par défaut | Ports typiques |
|---|---|---|---|
| `web` | Web (HTTPS / IMAPS / POP3S) | bleu | 443, 993, 995 |
| `smtp` | SMTP | ocre | 25, 587 |
| `ldap` | Service Discover / LDAP | violet | 389, 636 |
| `udp_video` | UDP (visioconférence / RTP) | rouge | 20000-40000 |
| `interne` | Flux applicatif interne (SOAP/REST) | gris | variable |
| `mesh` | Mesh (coordination inter-nœuds) | vert | interne uniquement |
| *(absent)* | Autre (repli automatique) | bleu | --- |

**Retirer un flux sans toucher au programme** : les flux étant désormais
déduits automatiquement, deux cas de figure ---
- **Le flux ne se produit vraiment pas** (ex. un pare-feu local bloque
  IMAPS/POP3S sur un nœud précis) : déclarer `blocked_protocols:` sur ce
  nœud (voir plus haut) --- le flux disparaît partout (schémas ET matrice).
- **Le flux existe mais encombre un schéma** : l'ajouter à
  `flow_diagram_exclusions:` en fin de fichier (voir plus haut) --- il
  reste dans la matrice exhaustive, seul son tracé sur les schémas est
  masqué.

**Personnaliser ou étendre la palette pour un client donné**, sans toucher
au catalogue par défaut (qui reste partagé par tous les clients), via la
clé optionnelle `flow_categories:` du fichier client :
```yaml
flow_categories:
  web:
    color: "1F77B4"        # surcharge la couleur par défaut de "web"
```

### Relations standard entre rôles (`templates/flow_relations.yaml`)

Ce fichier fait partie du **programme** (pas de la config client) : il
encode le savoir métier "qui parle à qui, sur quel protocole" pour une
infrastructure Carbonio standard (proxy -> mailstore, MTA IN/AUTH <-
pare-feu, tout consommateur LDAP -> Directory Master, etc.). C'est à
partir de ce catalogue et des nœuds/composants réellement déclarés dans la
config client que les flux sont dérivés --- voir la fonction
`derive_flows()` dans `generate_dat.py`. Pour ajouter une nouvelle relation
standard (ex. un nouveau composant qui consomme la base de données), il
suffit d'ajouter une règle à ce fichier, sans toucher au reste du
programme. La réplication LDAP Master/Replica n'y figure volontairement
pas (relation hors standard, sans intérêt sur les schémas).

### Schémas détaillés par type de flux

Dès que plus d'une catégorie de flux est utilisée, un schéma dédié est
généré automatiquement pour chacune (mêmes nœuds, mêmes positions que le
schéma d'ensemble, mais seuls les flux de cette catégorie sont tracés) ---
en plus du schéma d'ensemble qui reste affiché en premier. Objectif : éviter
qu'un schéma unique surchargé de toutes les catégories ne devienne
illisible sur une infrastructure de taille réelle.

### Tableau "Vue d'ensemble de l'infrastructure"

Généré automatiquement juste après la Topologie (§4.3/§4.4 selon le
document) : une ligne par nœud avec son/ses rôle(s), sa RAM, son nombre de
vCPU et son OS (`nodes[].sizing.os`). Distinct du tableau "Dimensionnement"
(qui garde son objectif propre : capacité de stockage et hypothèses de
charge).

### Grille multi-rangées par zone (`zones[].max_cols`)

Si une zone contient plus de nœuds que `max_cols` (3 par défaut), ils sont
automatiquement répartis en plusieurs rangées à l'intérieur de la même
zone (grille alignée en colonnes), plutôt que de s'étaler sur une largeur
illisible. Ajuster `max_cols` par zone selon la densité souhaitée ---
`max_cols: 2` convient bien à des rôles allant par paires (Proxy01/02, MTA
IN 01/02, etc.), `max_cols: 3` ou plus pour des pools plus larges
(Mailstores, Services).

**Notes générales** :
- Les `id` de `zones`/`nodes`/`network_equipment` doivent être cohérents
  entre les sections (un `zone:` référencé dans `nodes` doit exister dans
  `zones`). Le dernier élément de `network_equipment` (typiquement le
  pare-feu) est celui utilisé automatiquement comme point d'entrée/sortie
  des flux dérivés --- s'il est absent, les relations qui en dépendent
  (Internet -> Proxy/MTA IN/MTA AUTH, MTA OUT -> Internet) ne génèrent
  simplement aucun flux.
- Les flux qui partagent la même origine/destination réelle (ex. Chat et
  Tasks colocalisés sur le même nœud "application01", tous deux consommant
  le même port) sont automatiquement fusionnés en une seule ligne/flèche
  avec libellés combinés, aussi bien sur les schémas que dans la matrice
  exhaustive.
- Le schéma se redimensionne automatiquement pour ne jamais déborder de la
  page (largeur et hauteur), quelle que soit la taille de l'infrastructure.

## Ajouter un nouveau composant Carbonio

1. Ajouter une entrée dans `templates/components_catalog.yaml` (name, role,
   packages, default_ports, order).
2. (Optionnel) Créer `templates/partials/components/<id>.tex.j2` pour un
   rendu personnalisé. En son absence, `templates/partials/components/
   _generic.tex.j2` est utilisé automatiquement.
3. (Optionnel) Ajouter une entrée correspondante dans
   `templates/scope_catalog.yaml` pour que le composant apparaisse dans les
   sections "Périmètre" / "Services rendus".
4. Activer le composant dans les fichiers de config clients via
   `services.<id>: true`.

Aucune modification de `generate_dat.py` n'est nécessaire pour ajouter un
composant standard.

## Arborescence

```
dat-generator/
├── VERSION                              # numéro de version (ex. 1.0.0)
├── CHANGELOG.md                         # journal des versions
├── config/                             # UN fichier YAML par client
│   ├── client_exemple.yaml             # petite infra
│   ├── client_exemple_grande_infra.yaml # infra HA éclatée (test de charge)
│   └── logo_client_placeholder.png     # logo d'exemple (à remplacer par le vrai logo client)
├── templates/
│   ├── assets/
│   │   └── logo_zextras_services.png   # logo intégrateur par défaut
│   ├── components_catalog.yaml         # catalogue technique des composants (+ description commerciale)
│   ├── component_groups.yaml           # regroupements de composants (ex. MTA IN/OUT/AUTH)
│   ├── scope_catalog.yaml              # descriptions fonctionnelles (périmètre, §1.3)
│   ├── user_services_catalog.yaml      # descriptions "service rendu" orientées utilisateur final (§3.1)
│   ├── flow_categories.yaml            # catalogue des catégories de flux + couleurs
│   ├── flow_relations.yaml             # catalogue des relations standard (dérivation des flux)
│   ├── pca_pra_defaults.yaml           # procédures par défaut si pas de PCA/PRA spécifique
│   ├── preamble.tex.j2                 # en-tête LaTeX (styles, polices, logos)
│   └── partials/                       # une section = un fichier
│       ├── cover.tex.j2
│       ├── revisions.tex.j2
│       ├── intro.tex.j2
│       ├── stakeholders.tex.j2         # chapitre "Parties prenantes" (client + intégrateur)
│       ├── product.tex.j2              # chapitre "Solution Zextras Carbonio" + Licence
│       ├── functional_arch.tex.j2      # "Services rendus aux utilisateurs"
│       ├── infra_overview.tex.j2       # ouvre le chapitre 4 : tableau nœud/rôle/RAM/CPU/OS
│       ├── topology.tex.j2
│       ├── node_backup.tex.j2          # "Système de sauvegarde des nœuds" (avant la légende)
│       ├── flow_categories_ref.tex.j2  # légende des catégories, juste avant les schémas
│       ├── technical_arch_header.tex.j2 # schéma d'ensemble (sans flux) + schémas par catégorie
│       ├── components/
│       │   ├── _generic.tex.j2         # rendu par défaut (fallback : mesh,
│       │   │                           #   database, files, docs, tasks, monitoring)
│       │   ├── directory_master.tex.j2 # rendu personnalisé (renvoi croisé vers les replicas)
│       │   ├── directory_replica.tex.j2# rendu personnalisé (renvoi croisé vers le master)
│       │   ├── mailbox.tex.j2          # rendu personnalisé (rétention backup + HSM par nœud)
│       │   ├── proxy.tex.j2            # rendu personnalisé
│       │   ├── mta_in.tex.j2           # rendu personnalisé (SPF/DKIM/DMARC)
│       │   ├── mta_out.tex.j2          # rendu personnalisé (signature DKIM)
│       │   ├── mta_auth.tex.j2         # rendu personnalisé (contrôle d'accès)
│       │   ├── chat.tex.j2             # rendu personnalisé (note WebSocket)
│       │   └── videoconf.tex.j2        # rendu personnalisé (note ports UDP)
│       ├── ha_backup_security.tex.j2
│       ├── scheduled_operations.tex.j2 # "Opérations planifiées" --- ferme le chapitre 4
│       ├── dns.tex.j2                  # chapitre "DNS, légitimité et réputation"
│       ├── authentication.tex.j2       # chapitre "Authentification"
│       ├── autoprovisioning.tex.j2     # "Mécanisme d'ajout/Modification/Suppression..." (conditionnel)
│       ├── interfaces.tex.j2           # conditionnel (masqué si vide)
│       ├── exploitation.tex.j2
│       ├── nfr.tex.j2
│       ├── monitoring.tex.j2           # chapitre "Monitoring" (conditionnel, générique pour l'instant)
│       ├── support.tex.j2              # chapitre "Support" (sévérités, urgence)
│       ├── pra_pca.tex.j2              # chapitre "PCA/PRA" (indicateurs Oui/Non séparés)
│       ├── network_matrix.tex.j2       # matrice exhaustive des flux --- en fin de document
│       └── annexes.tex.j2              # simple tableau (nom/fichier/description)
├── tikz_builder.py                      # génère le schéma réseau dynamiquement
├── generate_dat.py                      # point d'entrée
└── build/                               # sorties générées (.tex / .pdf)
```
