# CLAUDE.md — Mémoire de projet

Ce fichier n'est pas une documentation fonctionnelle (voir `README.md` pour
la structure de config, `CHANGELOG.md` pour l'historique des versions). Il
capture le **raisonnement** derrière les décisions de conception qui ont
émergé au fil des échanges avec Julien (Zextras Services) — le genre de
contexte qui ne survit pas dans le code lui-même, mais qui évite de
redécouvrir (ou de reproduire) les mêmes hésitations.

## Philosophie générale du projet

**Le DAT documente le "quoi", pas le "pourquoi".** Décision explicite de
Julien : ce document décrit l'architecture actuelle telle que configurée,
pas la justification des choix passés. Si un besoin de traçabilité des
décisions techniques apparaît un jour, la bonne réponse est un document
**séparé et cumulatif** (façon ADR — Architecture Decision Record, écrit
une fois, jamais réécrit), pas un chapitre dans ce DAT régénéré. Raison
pratique : ce DAT est régénéré à chaque changement de config, alors qu'une
justification de choix est un fait historique figé — mélanger les deux
recréerait le problème qui a fait supprimer la section "Cartographie des
utilisateurs et domaines" (voir plus bas).

**Ce générateur cible les configurations standard, pas les cas exotiques.**
Exemple concret : la réplication LDAP Master/Replica n'est **jamais**
générée sur les schémas, même si elle existe techniquement dans Carbonio.
Julien a été explicite : "le cas d'une configuration exotique sort du
moteur de DAT, celui-ci ne doit être que pour les configurations standard
(1 master, 0..n replicas)". Ne pas essayer de généraliser au-delà de ce
périmètre sans une demande explicite.

**Priorité à la simplicité du code sur l'exhaustivité des fonctionnalités.**
Julien a explicitement fait marche arrière sur l'export `.odt` (implémenté,
fonctionnel, puis retiré) pour ne pas alourdir le programme. Si une
fonctionnalité ajoute de la complexité sans bénéfice clair, il vaut mieux
demander avant d'implémenter que de tout construire puis proposer de
retirer.

## Le moteur de dérivation dynamique des flux (le morceau le plus complexe)

Historiquement, les flux réseau étaient déclarés à la main (`flows:` dans
chaque config client). Julien a fait remarquer que l'essentiel était
déductible des `nodes[].components` + un savoir métier "qui parle à qui"
qui ne change pas d'un client à l'autre. Résultat : `flows:` **n'existe
plus du tout** (voir `templates/flow_relations.yaml` et
`derive_flows()` dans `generate_dat.py`).

Deux mécanismes **à ne jamais confondre** (Julien a insisté là-dessus) :

| | `nodes[].blocked_protocols` | `flow_diagram_exclusions` |
|---|---|---|
| Nature | Fait technique réel (le nœud bloque vraiment ce flux) | Choix de présentation, purement visuel |
| Effet | Retire le flux PARTOUT (schémas + matrice) | Retire seulement le tracé sur les schémas |
| Exemple donné | Un pare-feu local qui bloque SMTP sur un nœud précis | Désencombrer un schéma trop dense |
| La matrice exhaustive doit-elle refléter ce flux ? | Non, il n'existe pas | Oui, il existe réellement |

La matrice exhaustive de fin de document doit **toujours correspondre à la
réalité de terrain** ("pas simplement être le reflet d'une documentation
éditeur" — citation de Julien). C'est le critère qui a tranché plusieurs
décisions de conception dans cette zone.

**Risque accepté, délibérément non corrigé** : si une règle
`flow_diagram_exclusions` contient une faute de frappe (nœud inexistant,
catégorie mal orthographiée), elle ne filtre rien et rien ne le signale.
Julien : *"c'est un risque acceptable, c'est à l'opérateur de vérifier les
schémas et le paramétrage [...] on ne va pas lui enlever son expertise."*
Ne pas ajouter de système de validation/warning ici sans qu'il le demande
explicitement — c'est un choix, pas un oubli.

**Le mesh a le droit d'être moche.** Le composant `mesh` génère un maillage
complet (toutes les paires de nœuds qui l'hébergent), ce qui produit un
schéma dense (ex. 8 nœuds → 28 arêtes chez le client "Université
d'Amboise"). Accepté explicitement : *"il y a un schéma par type de
protocole, donc pas de souci, on laisse le mesh gribouiller son schéma."*
Ne pas essayer de simplifier/agréger le mesh sans qu'on le demande.

**Bugs déjà rencontrés et corrigés dans ce moteur** (à ne pas réintroduire
si le catalogue `flow_relations.yaml` est étendu) :
- Deux règles qui pointent vers le même nœud avec les mêmes ports mais des
  libellés différents (ex. Chat + Tasks colocalisés, tous deux sur 443)
  créaient des lignes dupliquées dans la matrice. La déduplication se fait
  maintenant sur la **signature de ports**, pas sur le libellé, en
  fusionnant les libellés des règles qui matchent.
- Les flux `mesh` n'ont pas de ports réels : leur donner un libellé
  explicite ("Interne (service discovery)") plutôt qu'une chaîne vide, qui
  retomberait sur le placeholder générique "[à préciser]" — trompeur, car
  ça laisse croire qu'il manque une information à saisir alors que c'est
  normal.

## Catalogues séparés par audience (ne pas les fusionner)

Trois catalogues décrivent les mêmes composants Carbonio, mais avec un
public différent — c'est intentionnel, pas une redondance à nettoyer :
- `components_catalog.yaml` (champ `role`) — description technique.
- `components_catalog.yaml` (champ `commercial`) — orientée décideur,
  affichée en intro de chaque sous-section de composant (pas dans un
  chapitre séparé qui les listerait toutes : décision explicite de Julien,
  "j'aimerais que cette description apparaisse en introduction de chaque
  brique et non pas dans un chapitre qui les liste").
- `user_services_catalog.yaml` — orientée utilisateur final ("qu'est-ce
  que je peux faire avec ça"). LDAP/Mesh/Database en sont volontairement
  absents : invisibles pour l'utilisateur, ils n'ont rien à faire dans
  "Services rendus aux utilisateurs" (mais restent mentionnés dans
  "Périmètre du document", §1.3, qui a un objet différent : documenter ce
  qui est couvert techniquement, pas ce que l'utilisateur perçoit).

## Sémantique "absent" vs "à compléter" (DNS)

Distinction fine à préserver : dans le chapitre DNS, l'**absence d'un
champ** dans le YAML (`spf`, `dkim_selector`, `dmarc`, ou `mx_records`
vide) signifie *"cet enregistrement n'existe vraiment pas"* et déclenche
une alerte rouge avec renvoi vers les conséquences. Ce n'est PAS la même
chose que les placeholders `[à compléter]` utilisés ailleurs dans le
document (qui signifient "pas encore renseigné, à faire par l'opérateur").
Julien : *"il faut donc trouver un moyen d'indiquer que l'entrée DNS
n'existe pas [...] peut-être enlever la ligne de configuration ?"* — oui,
c'est exactement le mécanisme retenu.

Les alias de domaine (`dns.domains[].alias_of`) sont rattachés à leur
domaine principal et affichés en sous-section (`\paragraph`) plutôt qu'en
entrée de premier niveau — pas de tableau séparé pour les alias.

## Regroupement automatique dans les schémas (sans champ de config dédié)

Les nœuds d'une même "famille de rôle" (ex. `proxy01`/`proxy02`,
`mta_in01`/`mta_in02`) s'alignent automatiquement en colonnes sur les
schémas, avec un encadré pointillé de regroupement visuel. Ce classement
est déduit du **nom du nœud** (suffixe numérique retiré, ex. `proxy01` →
famille `proxy`) — il n'y a **pas** de champ de config explicite pour ça.
Implication à garder en tête : ce mécanisme dépend d'une convention de
nommage (les nœuds d'une même famille doivent partager un préfixe). Si un
client nomme ses nœuds de façon incohérente, le regroupement visuel ne
fonctionnera pas comme attendu — c'est un compromis accepté pour éviter un
champ de config supplémentaire.

De la même manière, "Mesh" n'apparaît jamais dans le texte affiché *dans*
les boîtes des schémas (champ `components_display_diagram`, distinct de
`components_display` utilisé dans les tableaux) : il est présent sur
quasi tous les nœuds, le répéter dans chaque boîte n'apporte rien et
alourdit visuellement.

## Pièges LaTeX déjà rencontrés (pour ne pas les retrouver)

- **`\chapter` réinitialise le style de page en "plain"** sur sa première
  page par défaut (comportement du noyau LaTeX, pas un bug de ce projet).
  Corrigé via `\assignpagestyle{\chapter}{fancy}` (package `titlesec`).
- **`\titlepage` force `\thispagestyle{empty}`** — comportement gardé tel
  quel pour la couverture (pas de logo/pied de page dessus, volontaire).
- **`\paragraph` est un titre "run-in"** par défaut (s'enchaîne avec le
  texte sur la même ligne) — reformaté via `\titleformat` pour être sur sa
  propre ligne (utilisé pour les alias de domaine).
- **Ne jamais ré-échapper une valeur déjà échappée.** Bug rencontré :
  `client` (dict déjà passé dans `escape_latex`) était réutilisé comme
  valeur de repli pour l'historique des révisions, puis échappé une
  seconde fois → `\allowbreak` apparaissait en texte brut dans le PDF.
  Toujours garder une copie **brute** (`*_raw`) de tout dict destiné à
  servir de valeur par défaut plus loin dans le pipeline.
- **`escape_latex()` insère `\allowbreak` après les points/tirets** pour
  permettre la césure des hostnames/emails longs dans les cellules de
  tableau étroites. Les champs utilisés comme cible de `\href` (ex. email
  dans un `mailto:`) doivent rester **non échappés** pour le lien lui-même,
  avec une version séparée `*_display` échappée pour le texte visible.
- **`\includegraphics` a besoin d'un `\par` explicite** après lui dans un
  bloc centré, sinon le texte qui suit continue sur la même ligne au lieu
  de passer dessous (rencontré sur le logo client de la page de garde).

## Robustesse : config utilisateur mal formée

Un client réel a fait planter le programme (`AttributeError: 'str' object
has no attribute 'items'`) en fournissant une liste de chaînes simples là
où une liste de dictionnaires était attendue (`interfaces: ["Zabbix"]` au
lieu du format `{system, integration, protocol}`). Toute section de config
qui attend une **liste de dictionnaires** doit passer par
`esc_list_of_dicts()` (voir `generate_dat.py`), pas par un simple
`[esc_dict(x) for x in ...]` — ce dernier plante sur une entrée non-dict
au lieu de la traiter avec un repli raisonnable. Sections déjà protégées :
`interfaces`, `revisions`, `annexes`, contacts client/intégrateur,
`mx_records`, serveurs LDAP externes, plus un filtre `isinstance(dict)`
générique sur `nodes`, `flows` dérivés et `dns.domains`. **Toute nouvelle
section de config du même type doit suivre ce même pattern défensif.**

## Décisions rejetées ou abandonnées (ne pas re-proposer sans nouvelle raison)

- **Export `.odt`** : implémenté (schémas pré-rendus en PNG via
  compilations LaTeX `standalone` isolées, conversion par `pandoc`),
  fonctionnel et de bonne qualité visuelle, puis **retiré** à la demande de
  Julien pour limiter la complexité du programme. Si le besoin resurgit,
  l'implémentation de référence est dans l'historique Git — pas la peine
  de repartir de zéro, mais ne pas la réintroduire sans qu'on le redemande.
- **Validation des règles d'exclusion de flux** : volontairement absente
  (voir plus haut, risque accepté).
- **Généraliser au-delà des configurations LDAP standard** (1 master, 0..n
  replicas) : hors périmètre assumé du générateur.

## Mise à jour DNS : outil séparé, jamais intégré à la génération par défaut

`update_dns_from_zone.py` résout MX/SPF/DMARC en direct et **réécrit la
config** (pas une résolution "à la volée" à chaque compilation). Décision
directement liée au principe de déterminisme du DAT (voir plus haut) :
Julien a d'abord demandé une récupération DNS pendant la génération, on a
discuté des risques (document non-reproductible, DNS actuel qui peut
différer de l'architecture *cible* documentée, dépendance réseau pour une
opération qui n'en avait pas besoin), et convergé sur un outil séparé qui
**persiste** le résultat dans le fichier de config --- qui reste ainsi la
seule source de vérité, versionnée, review-able via `git diff` avant tout
commit. Le flag `--update-dns` de `generate_dat.py` n'est qu'un raccourci
pratique qui appelle ce même script avant de générer ; il ne change pas
le principe.

**DKIM explicitement exclu** de cet outil (décision de Julien) : le
sélecteur reste une saisie manuelle (non "découvrable" en DNS sans le
connaître déjà), et la validité du contenu de l'enregistrement DNS DKIM
est confiée à l'AS/AV et aux outils de monitoring --- pas à ce générateur.

**Piège rencontré en testant** : un domaine qui déclare "je n'accepte
aucun e-mail" utilise un MX dit "nul" (RFC 7505 --- `exchange` vaut `.`,
`preference` vaut `0`). Le traiter naïvement (`str(exchange).rstrip('.')`)
produit un hostname **vide**, trompeur dans le DAT. Représenté
explicitement par `"."` à la place.

## Le DEX : contenu comme données, pas comme templates

Contrairement aux composants du DAT (qui ont des besoins structurels
réellement différents d'un composant à l'autre, ce qui justifie un fichier
`.tex.j2` par composant), les opérations du Document d'Exploitation sont
**structurellement quasi-identiques** (titre, description, commande(s),
parfois un tableau d'options, parfois un avertissement). Julien a
explicitement demandé qu'ajouter une nouvelle opération n'exige *aucune*
modification de code --- ça a orienté vers un seul template générique
(`operation.tex.j2`) piloté par des données YAML, plutôt que de reproduire
le pattern "un fichier par brique" du DAT. Les briques sont auto-découvertes
par scan de dossier (`briques/*.yaml`, triées par nom de fichier), jamais
listées en dur dans le code --- **vérifié concrètement** en ajoutant puis
retirant une brique de test pendant le développement, sans toucher au
code entre les deux.

**GAL et réindexation des comptes** ont été explicitement écartées de
cette première version par Julien ("osef, laisse tomber" / "on l'ajoutera
plus tard") --- ne pas les ajouter de sa propre initiative sans qu'il le
redemande. La commande de réindexation (`zmprov rim`) a été vérifiée
comme réelle avant d'être proposée, mais n'a pas été intégrée puisqu'elle
n'a pas été demandée.

**Pièges rencontrés en construisant le DEX** :
- **`op.items` en Jinja capte la méthode `dict.items()` de Python**, pas
  la clé `"items"` du dictionnaire --- erreur `'builtin_function_or_method'
  object is not iterable`. Piège classique de Jinja avec les noms `items`,
  `keys`, `values`, `update`... Renommé en `bullet_items` pour éviter toute
  collision future avec un nom de méthode dict.
- **`graphicx` et `amssymb` ne sont pas inclus implicitement** dans un
  préambule qui ne charge pas `tikz` (le DAT les obtient indirectement via
  `\usepackage{tikz}`). Un préambule minimal doit les déclarer
  explicitement --- sans quoi `\includegraphics` et `\boxtimes`/`\square`
  échouent avec des messages d'erreur LaTeX assez confus (cascade de
  "Missing $ inserted" qui n'ont rien à voir avec la vraie cause).
- **Les commandes shell (`commands`/`example_output`) ne doivent jamais
  passer par `escape_latex()`** --- elles sont insérées telles quelles
  dans un environnement `lstlisting`, qui ne nécessite aucun échappement
  et gère nativement `_`, `%`, `$`, `{`, `}`. Tous les AUTRES champs texte
  (title, description, warning, options_table...) doivent au contraire
  être échappés normalement.
- **Sans niveau `\section` intermédiaire entre `\chapter` (brique) et les
  opérations, LaTeX numérote en "3.0.10" au lieu de "3.10"** (chapitre 3,
  section implicite 0, sous-section 10). Chaque opération est numérotée au
  niveau `\section` directement (pas `\subsection`) pour éviter cet
  artefact cosmétique.

## Le DEX personnalisé par client : réutilise le contexte du DAT, ne le duplique pas

`generate_dex.py --client config/x.yaml` appelle directement
`generate_dat.build_context()` pour obtenir `stakeholder_client`,
`stakeholder_integrator` (logos déjà copiés, contacts déjà échappés) ---
plutôt que de réimplémenter cette logique côté DEX. Le chapitre "Parties
prenantes" est le fichier `templates/partials/stakeholders.tex.j2` du DAT
**tel quel**, chargé via un `FileSystemLoader` qui cherche dans
`templates_dex/` puis dans `templates/`. Concrètement, le DEX ne devrait
jamais dupliquer une logique déjà présente côté DAT si elle est
directement importable/réutilisable --- c'est la version concrète du
"script au-dessus des trois" évoqué au démarrage du second projet.

**Deux champs distincts sur une brique, à ne pas confondre** (Julien a
validé cette distinction explicitement) :
- `services: [...]` --- décide si la brique **apparaît** en mode
  `--client` (comparé aux `services: {...}` activés dans la config
  client). Absent = brique universelle, toujours incluse. Aucun effet en
  mode générique (tout est toujours inclus).
- `components: [...]` --- décide quels **nœuds sont affichés** comme
  concernés par la brique (résolu dynamiquement depuis `nodes[].components`
  de la config client), sans jamais masquer la brique elle-même. Aucun
  effet en mode générique (pas de config client à interroger).

**Classification par défaut dépendante du mode, pas figée dans le YAML** :
`config/dex_meta.yaml` ne fixe plus `confidentiality:` en dur --- si le
champ est absent, le code choisit "public" en mode générique et "client"
en mode `--client`. Rationale : un DEX personnalisé contient de vraies
informations d'infrastructure (topologie, hostnames, domaines) qui n'ont
pas leur place dans un document coché "diffusable librement". Le
paragraphe "Propriété intellectuelle et usage autorisé" (mode client
uniquement) découle du même raisonnement --- **volontairement absent du
DAT**, qui n'en a pas besoin (Julien l'a confirmé explicitement).

**Le préambule LaTeX est désormais partagé à 100 % entre DAT et DEX**
(`templates/preamble.tex.j2`) --- le DEX n'a plus son propre préambule.
Deux paquets ont dû être ajoutés à ce fichier partagé pour les besoins du
DEX (`listings` pour les blocs de commande, `amssymb` pour les cases à
cocher de confidentialité) : ils sont inertes pour le DAT, qui ne les
utilise pas, mais en hérite --- accepté comme un coût de mutualisation
négligeable plutôt que de dupliquer un second préambule presque identique.

## Toujours vérifier l'état réel du dépôt avant de patcher (leçon répétée deux fois)

Ce problème s'est produit **deux fois** : un patch livré et validé sur
clone frais s'est révélé inapplicable, parce que le dépôt de Julien avait
entre-temps évolué autrement que prévu (patches appliqués manuellement,
dans un ordre ou une forme différente de ce qui était supposé). La seule
façon fiable de repartir dans ce cas : **cloner frais et inspecter
directement les fichiers clés** (`grep` sur une fonction/un flag
caractéristique, `cat` sur les fichiers concernés) avant de faire une
seule modification --- jamais supposer l'état d'un dépôt à partir des
patches qu'on croit avoir livrés. Ne jamais reconstruire "from scratch"
par hypothèse : partir du contenu réel, même si ça veut dire relire
plusieurs fichiers avant de coder quoi que ce soit.

## Name vs Long Name : uniformisé sur long_name partout

Le DAT affichait `client.name` (court) sur sa couverture, mais
`stakeholder_client.long_name` (long) dans son propre chapitre "Parties
prenantes" --- incohérence interne au DAT, repérée par Julien en
comparant une page du DAT à une page du DEX (qui utilisait déjà
`long_name` partout). Corrigé en uniformisant sur `stakeholder_client.
long_name` (couverture DAT + `pdftitle`) --- ce champ retombe déjà sur le
nom court si `long_name` n'est pas renseigné dans la config (voir
`_build_stakeholder_ctx`), donc aucune configuration existante ne casse.
Règle à retenir pour toute nouvelle section affichant l'identité du
client : préférer systématiquement `stakeholder_client.long_name` à
`client.name`, sauf contrainte d'espace explicite (ex. en-tête compact
sur chaque page, qui reste sur le nom court délibérément).

## Où regarder pour le reste

- `README.md` — structure complète du fichier de configuration, toutes
  les clés disponibles, arborescence du projet.
- `CHANGELOG.md` — historique version par version, y compris les
  changements de rupture (breaking changes) signalés explicitement.
- `templates/flow_relations.yaml` — catalogue des relations standard
  (le "qui parle à qui" utilisé par le moteur de dérivation).
- `templates/components_catalog.yaml`, `component_groups.yaml`,
  `user_services_catalog.yaml`, `flow_categories.yaml`,
  `pca_pra_defaults.yaml` — catalogues internes au programme, communs à
  tous les clients (à distinguer des fichiers `config/*.yaml`, propres à
  chaque client).
