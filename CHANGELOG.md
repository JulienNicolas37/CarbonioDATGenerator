# Journal des versions --- Générateur de DAT Carbonio

Les versions antérieures à 1.0.0 n'ont pas été formellement numérotées
(phase de conception itérative). À partir de 1.0.0, chaque livraison porte
un numéro de version répercuté dans le nom de l'archive
(`dat-generator-vX.Y.Z.zip`), pour permettre un suivi simple dans le temps.

## 1.11.0 --- 2026-08-12

- **`config/dex_meta.yaml` supprimé** --- rédacteur, vérificateur,
  révisions et confidentialité du DEX viennent désormais exclusivement du
  fichier de config client (`client.author`, `client.verificateur`,
  `revisions:`, `client.classification`), exactement comme pour le DAT.
  Aucun fichier de configuration séparé à maintenir pour le DEX.
- Flag `--meta` retiré de `generate_dex.py` (devenu sans objet).
- En mode générique (sans `--client`), ces informations retombent sur des
  placeholders explicites (`"[à préciser]"`) plutôt que sur un fichier de
  config annexe.

## 1.10.0 --- 2026-08-12

- **Nouvelle structure de dossiers de sortie** : chaque client a
  désormais son propre dossier (nom court), avec le PDF final à sa
  racine et tous les fichiers intermédiaires (`.tex`, `.aux`, `.log`,
  `.out`, `.toc`, logos copiés) dans un sous-dossier `generation/` ---
  jamais suivi par git. Le DAT et le DEX d'un même client
  (`generate_dex.py --client ...`) partagent ce même dossier.
- Par défaut (`--outdir` non précisé), les documents client vont dans
  `build/customers/` (non suivi par git, comportement inchangé) ; les
  deux exemples fournis restent visibles dans le dépôt via `--outdir
  build` explicite (PDF uniquement --- le `.tex` des exemples n'est plus
  suivi, voir `CLAUDE.md` pour le détail de ce compromis).
- Le mode générique du DEX (sans `--client`) est inchangé : toujours
  plat dans `build/dex/`, PDF et `.tex` suivis par git.
- `.gitignore` renforcé : `generation/` ignoré à tout niveau, plus
  `*.aux`/`*.log`/`*.out`/`*.toc` ignorés globalement par sécurité.

## 1.9.0 --- 2026-08-12

- **Correction Name/Long Name** : la couverture du DAT affichait
  `client.name` (court) alors que le chapitre "Parties prenantes" du DAT
  lui-même, et le DEX, affichaient déjà `stakeholder_client.long_name`
  (long) --- incohérence corrigée en uniformisant sur `long_name`
  (rétrocompatible : replié automatiquement sur le nom court si
  `long_name` n'est pas renseigné).
- **`client.verificateur`** (nouveau champ) --- affiché sur la couverture
  du DAT, et repris automatiquement par le DEX en mode `--client` (plus
  aucune duplication avec `config/dex_meta.yaml`).
- **Rédacteur/vérificateur/révisions centralisés** : en mode
  `generate_dex.py --client`, ces informations viennent systématiquement
  du fichier de config client (via `generate_dat.build_context()`), plus
  jamais de `dex_meta.yaml` --- une seule source de vérité à maintenir au
  quotidien.
- **Confidentialité et propriété intellectuelle ajoutées au DAT**
  (partials partagés `confidentiality.tex.j2` / `ip_notice.tex.j2`,
  réutilisés par le DEX) --- dérivées de `client.classification`.
- **Catalogue Carbonio Community Edition** (`templates/
  carbonio_editions.yaml`) --- fonctionnalités confirmées absentes de la
  CE (sauvegarde native, HSM, legal hold, MDM, white-labeling ; catalogue
  volontairement conservateur, à étendre si besoin). Nouveaux champs
  `client.carbonio_edition` (`ce`/`advanced`) et
  `client.carbonio_ce_version` :
  - Affichage de l'édition dans le chapitre "Solution Zextras Carbonio" du DAT ;
  - Alerte si HSM configuré alors que le client est en CE ;
  - La brique "Sauvegarde et restauration" du DEX disparaît automatiquement
    pour un client en CE (`ce_feature: "backup"`).
- **Chapitre 1 du DEX restructuré** ("Introduction et cadrage" : Objet du
  document, Confidentialité, Propriété intellectuelle, Approbations) ---
  même structure que le DAT. L'historique des révisions devient son
  propre chapitre non numéroté (réutilisé du DAT en mode `--client`),
  aligné sur la structure du DAT.
- Intros pédagogiques ajoutées aux briques qui en étaient dépourvues.

## 1.8.0 --- 2026-08-11

- **DEX personnalisable par client**, via `generate_dex.py --client
  config/client.yaml` :
  - Filtrage des briques par service activé (`services:` dans la brique
    --- absent = brique universelle, toujours incluse) ;
  - Liste des nœuds concernés par chapitre (`components:` dans la brique,
    résolu dynamiquement depuis la topologie réelle du client) ;
  - Chapitre "Parties prenantes" et logos réutilisés directement du DAT
    (même template, même mécanisme) ;
  - Paragraphe de propriété intellectuelle / usage autorisé (mode client
    uniquement --- absent du DAT, qui n'en a pas besoin) ;
  - Classification par défaut intelligente : "Public" en mode générique,
    "Client" en mode `--client` (peut être explicitement surchargée dans
    `config/dex_meta.yaml`).
- **Style et ouverture de document unifiés avec le DAT** : le DEX
  réutilise désormais directement `templates/preamble.tex.j2` (police,
  couleurs, en-tête/pied de page, logos) et le même modèle de page de
  garde --- plus de style bespoke propre au DEX.
- Le préambule partagé gagne `listings` (blocs de commande du DEX) et
  `amssymb` (cases à cocher) --- extensions inertes pour le DAT, qui ne
  les utilise pas mais en hérite sans impact.

## 1.7.0 --- 2026-08-10

- **Première version du générateur de Document d'Exploitation (DEX)**,
  `generate_dex.py` --- second outil du dépôt, sur le même modèle
  architectural que le DAT (catalogues YAML auto-découverts, template
  générique, préambule/branding partagés).
- **Mécanisme d'auto-découverte** : les "briques" (chapitres) sont des
  fichiers YAML dans `briques/*.yaml`, chargés automatiquement au
  démarrage (triés par nom de fichier). Ajouter une brique = déposer un
  fichier. Ajouter une opération à une brique existante = ajouter une
  entrée dans son fichier. **Aucune des deux actions ne nécessite de
  modifier le code** --- vérifié concrètement en ajoutant puis retirant
  une brique de test pendant le développement.
- Deux "squelettes" génériques disponibles par brique : `operations`
  (titre, description, prérequis, liste à puces, commande(s), tableau
  d'options, sortie d'exemple, avertissement) et `reference_table`
  (tableau de référence simple, ex. chapitre "Fichiers de logs").
- Contenu initial repris fidèlement du document d'exploitation existant
  (`20250207-Administration_CLI_Carbonio_v3.pdf`) : opérations courantes,
  gestion des comptes/domaines/listes de distribution/alias (`zmprov`),
  attributs Carbonio, remplacement de certificat SSL, restauration de
  compte, partage racine, fichiers de logs. **Volontairement absents pour
  cette première version** : réindexation des comptes et génération de la
  GAL (à ajouter plus tard).
- Réutilise directement `escape_latex()` et `compile_pdf()` du DAT (premier
  pas concret vers le socle commun évoqué --- pas encore de refactor
  complet, mais plus de duplication de cette logique).

## 1.6.0 --- 2026-08-10

- **Nouveau script `update_dns_from_zone.py`** : met à jour MX/SPF/DMARC
  d'un fichier de configuration client directement depuis le DNS réel
  (jamais le DKIM --- le sélecteur reste saisi à la main). Réécriture en
  place via `ruamel.yaml` (préserve commentaires et mise en forme).
  Utilisable seul, ou via le nouveau flag `--update-dns` de
  `generate_dat.py` pour tout faire en une seule commande.
- Gère correctement le cas du "MX nul" (RFC 7505, domaine qui déclare
  explicitement n'accepter aucun e-mail) plutôt que de produire un champ
  vide trompeur.
- Nouvelles dépendances **optionnelles** (uniquement pour cette
  fonctionnalité) : `dnspython`, `ruamel.yaml`.

## 1.5.0 --- 2026-08-07

**⚠️ Changement de rupture (breaking change)** : la section `flows:` du
fichier de configuration client **n'existe plus et n'est plus lue**. Les
flux réseau sont désormais **déduits automatiquement** des nœuds/composants
déclarés (`nodes[].components`) et d'un catalogue de relations standard
fourni avec le programme (`templates/flow_relations.yaml`) --- proxy vers
chaque mailstore, chaque nœud consommateur de LDAP vers le Directory
Master, pare-feu vers chaque MTA IN/AUTH/Proxy, etc. Toute config
existante avec une section `flows:` verra celle-ci simplement ignorée (les
deux fichiers d'exemple ont été migrés).

Nouveaux leviers de configuration, à la place de `flows:` :
- **`nodes[].blocked_protocols`** (liste de catégories) --- blocage
  TECHNIQUE réel d'un flux sur un nœud précis (ex. pare-feu local) : le
  flux disparaît partout (schémas ET matrice), puisqu'il ne se produit pas
  réellement.
- **`flow_diagram_exclusions`** (en fin de fichier client) --- exclusion
  PUREMENT VISUELLE sur les schémas (le flux reste dans la matrice
  exhaustive, qui doit toujours refléter la réalité de terrain).
- **`protocol_schemas`** (Oui/Non par catégorie) --- décide quelles
  catégories ont un schéma dédié dans le DAT.

Autres ajouts de cette version :
- **Catégorie `mesh`** : maillage complet automatique entre tous les nœuds
  hébergeant le composant `mesh`, sur son propre schéma dédié.
- **Protection anti brute-force** (`authentication.brute_force_protection`,
  type fail2ban) --- affichée dans les politiques de sécurité du chapitre
  Authentification.
- La réplication LDAP Master/Replica n'est volontairement plus représentée
  sur les schémas (relation hors standard).

Changements accumulés depuis la 1.4.0, jamais encore packagés :
- Nouvelle description du produit Zextras Carbonio (§2.1 Présentation
  générale) et de l'intégrateur Zextras Services (chapitre Parties
  prenantes).
- Suppression de la section "Cartographie des utilisateurs et domaines"
  (données non dynamiques / instantané d'exploitation, hors périmètre d'un
  DAT --- voir discussion).
- Colonne "IP fixe (frontal)" renommée en "IP publique" dans le tableau de
  topologie.
- Retrait de toute mention de "Janus" (détail d'implémentation non
  pertinent pour le client) --- le composant reste "Visioconférence (Video
  Server)".

## 1.4.0 --- 2026-08-06

- **Alias de domaine** (`dns.domains[].alias_of`) : un alias est désormais
  présenté comme une sous-section de son domaine principal, avec
  explication du concept en début de chapitre DNS.
- **Alertes rouges automatiques** si un domaine (principal ou alias) n'a
  pas de MX, SPF, DKIM ou DMARC --- détecté par simple absence du champ
  dans la configuration (pas besoin d'un marqueur spécial : retirer la
  ligne suffit).
- **Conséquences par type d'enregistrement DNS** (MX, SPF, DKIM, DMARC)
  ajoutées dans les explications de référence, avec renvoi croisé depuis
  chaque alerte.
- **Correction de robustesse** : le programme plantait
  (`AttributeError: 'str' object has no attribute 'items'`) si une section
  de config attendant une liste de dictionnaires (`interfaces`,
  `revisions`, `annexes`, contacts, enregistrements MX, serveurs LDAP
  externes...) contenait par erreur de simples chaînes de texte. Ces cas
  sont maintenant gérés proprement (valeur affichée telle quelle) plutôt
  que de faire planter la génération. Protection générale ajoutée sur
  `nodes`, `flows` et `dns.domains` contre le même type d'erreur de format.

## 1.3.0 --- 2026-08-05

- **IP fixe (publique)** pour les nœuds frontaux (`nodes[].public_ip`) ---
  nouvelle colonne dans le tableau "Topologie retenue".
- **Méthode de répartition de charge** (`load_balancing: {proxy, mta_in,
  mta_out, mta_auth}`) --- affichée en fin de sous-section de chaque
  composant concerné, uniquement si renseignée.
- **Domaines dont le DKIM est géré par l'AS/AV** (`antispam_antivirus.
  dkim_domains`) --- nouvelle colonne "Signature portée par" (Carbonio ou
  AS/AV) dans le tableau DKIM par domaine.

## 1.2.0 --- 2026-08-05

- **Logo client centré sur la page de garde** (au-dessus du titre), en plus
  de sa présence en en-tête sur les pages suivantes.
- **Ligne "Prestataire"** ajoutée au tableau de la page de garde, entre
  "Périmètre" et "Rédacteur" --- alimentée automatiquement depuis
  `integrator.long_name`.

## 1.1.0 --- 2026-08-05

- **Logos sur toutes les pages** : correction du comportement standard de
  LaTeX qui réinitialisait le style de page en "plain" (sans logos) sur la
  première page de chaque chapitre. Utilise `\assignpagestyle` (package
  `titlesec`) pour conserver le style "fancy" (logos) partout.
- **Nouveau pied de page**, actif à partir de la première page du chapitre
  1 jusqu'à la fin du document (aucun pied de page sur la couverture,
  l'historique des révisions et le sommaire) : "Document du \<date de
  génération\>" à gauche, "Page X / Y" à droite.
- **Nouvel exemple client** : `config/client_exemple_grande_infra.yaml`
  utilise désormais "Université d'Amboise" (avec son logo) et deux
  domaines de messagerie distincts (`univ-amboise.fr` pour le personnel,
  `etu.univ-amboise.fr` pour les étudiants), pour un cas de test plus
  parlant qu'un nom générique.

## 1.0.0 --- 2026-08-05

Première version formellement versionnée. Consolide l'ensemble des
itérations précédentes et ajoute :

- **Retrait de l'export `.odt`** (revenu sur cette fonctionnalité pour
  limiter la complexité du programme).
- **Police Open Sans** dans tout le document (compilation via `xelatex` +
  `fontspec`, au lieu de `pdflatex`).
- **En-têtes et pieds de page avec logos** : logo du client (fourni à côté
  du fichier de configuration) et logo Zextras Services (fourni avec le
  programme), plus coordonnées de l'intégrateur en pied de page.
- **Identité du client et de l'intégrateur** : nouvelle section "Parties
  prenantes" avec nom long, description, site web, adresse postale et
  liste de contacts (nom, rôle, e-mail, téléphone) --- pour le client ET
  pour Zextras Services (préremplie).

## Avant 1.0.0 (non versionné)

Mise en place progressive de l'ensemble des fondations~: génération
LaTeX modulaire depuis une config YAML, schéma réseau TikZ généré
dynamiquement (zones, colonnes par rôle, catégories de flux colorées,
équipements réseau), catalogue de composants Carbonio (Mesh, Directory
Master/Replica, Database, Mailstore, Proxy, MTA IN/OUT/AUTH, Files, Docs,
Chat, Visioconférence, Tasks, Monitoring), chapitres Solution Carbonio,
Licence, DNS/réputation/SPF/DKIM/DMARC, Authentification, Auto-
provisionnement, Support, PCA/PRA, sauvegarde par nœud, opérations
planifiées, matrice exhaustive des flux réseau.
