# Journal des versions --- Générateur de DAT Carbonio

Les versions antérieures à 1.0.0 n'ont pas été formellement numérotées
(phase de conception itérative). À partir de 1.0.0, chaque livraison porte
un numéro de version répercuté dans le nom de l'archive
(`dat-generator-vX.Y.Z.zip`), pour permettre un suivi simple dans le temps.

## 1.17.3 --- 2026-08-20

- **Liste à puces** pour l'avertissement de bonne pratique DKIM
  consolidé (chapitre AS/AV) --- l'énumération des domaines concernés
  était auparavant intégrée dans une seule phrase, illisible dès que
  plusieurs domaines étaient concernés. La version par domaine (un seul
  domaine à la fois) reste une phrase simple, inchangée.

## 1.17.2 --- 2026-08-20

- **Reformulation** des avertissements de bonne pratique DKIM (par
  domaine et consolidé dans le chapitre AS/AV) --- registre plus
  professionnel, sans répétition avec le préfixe "Attention" déjà ajouté
  par la macro d'avertissement.

## 1.17.1 --- 2026-08-20

- **Chapitre AS/AV corrigé** : la phrase par défaut affichée quand aucun
  domaine n'a son DKIM porté par l'AS/AV affirmait à tort que "Carbonio
  gère le DKIM pour tous les domaines" --- faux dès qu'un domaine est
  porté par un nœud dédié hors Carbonio (ex. un relais tiers). Remplacée
  par une phrase neutre qui ne présume pas du porteur réel.
- **Avertissement de bonne pratique DKIM consolidé** : affiché désormais
  aussi dans le chapitre AS/AV lui-même (pas seulement par domaine) si
  l'AS/AV filtre le courrier sortant sans porter le DKIM d'au moins un
  domaine --- liste les domaines concernés.

## 1.17.0 --- 2026-08-20

- **Tâches planifiées (cron) par défaut du mailstore** --- catalogue dans
  `templates/components_catalog.yaml` (`mailbox.default_scheduled_tasks`),
  les 10 tâches réelles transmises par Julien, avec les 3 descriptions
  confirmées auprès d'une source officielle Zextras (les 7 autres restent
  `"[à préciser]"` plutôt que d'inventer).
- **Surcharge par mailstore** (pas globale) : `nodes[].
  scheduled_tasks_overrides.<nom_de_tâche>.{cron, disabled}`.
- Si tous les mailstores s'accordent sur une tâche, elle apparaît dans un
  tableau unique "pour l'ensemble des mailstores" (chapitre "Opérations
  planifiées") ; si un mailstore diverge, elle sort dans une présentation
  détaillée par nœud --- affichée à la fois dans ce chapitre et dans la
  section propre à chaque mailstore concerné (duplication volontaire).
- Correction d'un débordement visuel dans les tableaux : les identifiants
  camelCase sans espace ni tiret (noms de tâches cron Carbonio) n'avaient
  aucun point de rupture pour passer à la ligne --- nouveau helper
  `_break_camel()`.

## 1.16.0 --- 2026-08-19

- **`config/reference_full.yaml`** (nouveau) : fichier de référence
  exhaustif listant tous les champs de configuration disponibles --- à
  utiliser comme point de départ pour un nouveau client, ou comme point
  de comparaison (`diff`) pour repérer les nouveaux champs disponibles
  lors d'une montée de version. Sera tenu à jour à chaque nouvelle
  version qui introduit ou modifie un champ (voir `CLAUDE.md`).
- **Annotation visuelle de l'AS/AV** sur les boîtes des schémas quand
  `antispam_antivirus.deployment` pointe vers un nœud ou un pool
  existant (plutôt que "external") --- affiché en plus des composants
  habituels du nœud.
- **Chapitre "Contraintes et exigences non fonctionnelles" corrigé** :
  seule la disponibilité (`sla.availability`) était alimentée par la
  config, tout le reste était un texte figé dans le template depuis le
  début du projet. Nouvelle section `nfr:` (performance, conformité,
  souveraineté, réversibilité).
- **`user_protocols`** (nouveau) : `imap`/`pop`/`smtp_submission`,
  distincts de l'existence des composants (`services.proxy`/
  `services.mta_auth`) --- répercuté sur la liste "Protocole(s) d'accès
  autorisés" du chapitre fonctionnel. Tout à `true` par défaut si absent.
- **`network_equipment[].blocked_ports`** (nouveau) : retire PARTOUT
  (schémas et matrice) tout flux utilisant un port bloqué sur l'équipement
  concerné, même philosophie que `nodes[].blocked_protocols`.

## 1.15.0 --- 2026-08-19

- **Relais de messagerie tiers (non-Carbonio)** : nouveau composant
  `mail_relay` (catalogue + template dédié minimal), à déclarer comme un
  nœud normal.
- **`load_balancer_pools`** (nouveau) : un identifiant qui désigne
  plusieurs nœuds à la fois (répartition de charge / haute
  disponibilité), réutilisable comme porteur DKIM, comme déploiement de
  l'AS/AV, ou comme maillon dans un chemin de flux e-mail.
- **`antispam_antivirus.deployment`** (nouveau) : "external" (défaut,
  boîte symbolique dans les schémas) | id de nœud | id de pool.
  Avertissement rouge si l'id ne correspond à rien de déclaré.
- **⚠️ Changement de rupture** : `antispam_antivirus.dkim_domains`
  supprimé, remplacé par `dns.domains[].dkim_carrier` (absent = Carbonio ;
  `"antispam_antivirus"` ; ou un id de nœud/pool précis). Une seule
  déclaration par domaine alimente automatiquement le récapitulatif
  AS/AV, le détail DNS du domaine, et la section du nœud/relais porteur.
  Avertissement rouge si l'id ne correspond à rien de déclaré, et
  **avertissement de bonne pratique** si l'AS/AV filtre le courrier
  sortant sans être lui-même le porteur DKIM du domaine.
- **`email_flow_paths`** (nouveau) : chemin de flux e-mail personnalisé
  (notation `protocole:sens:maillon1:maillon2:...`, seul `smtp` pris en
  charge pour l'instant) --- remplace le lien standard direct
  MTA↔pare-feu pour les nœuds concernés, ajoute les maillons déclarés
  (relais, AS/AV...) à la place. Le maillon spécial `antispam_antivirus`
  se résout vers son déploiement réel, y compris une boîte symbolique
  "AS/AV externe" dans les schémas si `deployment: external`.
- Les deux fichiers d'exemple ont été mis à jour avec une démonstration
  réaliste (relais en haute disponibilité, AS/AV déployé sur un pool de
  MTA OUT, porteurs DKIM différenciés par domaine).
- Correction d'un bug latent dans `label_for()` (générateur de la matrice
  exhaustive de flux) : un `label` de nœud contenant du LaTeX brut était
  rééchappé, produisant du code LaTeX littéral affiché dans le PDF.

## 1.14.0 --- 2026-08-13

- **⚠️ Changement de rupture** : `client.version` et `client.date` sont
  supprimés. La case "Version du document"/"Date" de la couverture (DAT
  et DEX) reprend désormais systématiquement la **dernière entrée** de
  `revisions:` --- une seule source à maintenir pour la version du
  document, au lieu de deux potentiellement incohérentes. Le repli par
  défaut (si `revisions:` est absent) ne dépend plus de `client.version`/
  `client.date` non plus.
- Les deux fichiers d'exemple (`config/client_exemple*.yaml`) ont reçu un
  historique de révisions réaliste à 3 entrées, pour qu'un nouveau client
  réel parti de l'un de ces fichiers dispose d'un exemple concret plutôt
  que d'une section absente.

## 1.13.2 --- 2026-08-13

- **DEX** : le chapitre "Plan de maintenance --- synthèse" est désormais
  placé après "Parties prenantes" (juste avant la première brique, ex.
  "Opérations courantes") plutôt qu'avant --- en mode générique (pas de
  chapitre "Parties prenantes"), l'ordre était déjà correct.
- **Documentation uniquement** : ajout au README de la procédure pour
  éditer directement un `.tex` généré et le recompiler sans repasser par
  le générateur (`latexmk -xelatex`, y compris le mode "preview continu"
  `-pvc`) --- aucun outil à développer, `latexmk` fait déjà exactement
  ça et est fourni par toute distribution TeX Live standard.

## 1.13.1 --- 2026-08-13

- **Rattrapage** : `carbonio_edition` vivait encore sous `client:` alors
  qu'il devait migrer sous `product:` (`product.edition`) --- seul son
  affichage avait été déplacé précédemment, pas le champ de config
  source. Corrigé dans `generate_dat.py` et `generate_dex.py` (filtrage
  CE des briques du DEX), ainsi que dans les deux configs d'exemple et le
  README.

## 1.13.0 --- 2026-08-12

- **Champs `_raw` pour le DEX** (`description_raw`, `prerequisites_raw`,
  `explanation_raw`, `warning_raw`) --- variante non échappée d'un champ
  texte existant, pour écrire du LaTeX enrichi (gras, listes, macros...)
  directement dans une brique. Garde-fou léger (accolades non balancées)
  --- avertissement en console à la génération, jamais de blocage.
- **Bloc `attributes:` par opération** (type, fréquence, criticité,
  automatisable, interruption, contrôle attendu, durée estimée, fenêtre
  recommandée) --- optionnel, tous les champs sont eux-mêmes optionnels.
- **Rappel compact** des attributs sous le titre de chaque opération qui
  en porte.
- **Nouveau chapitre "Plan de maintenance --- synthèse"**, généré
  automatiquement en tête de document (juste après "Introduction et
  cadrage") : tableau récapitulatif de toutes les opérations portant un
  bloc `attributes`, toutes briques confondues, en page paysage. Aucune
  configuration supplémentaire nécessaire au-delà du bloc `attributes`
  lui-même.

## 1.12.0 --- 2026-08-12

- **⚠️ Changement de rupture** : l'authentification (méthode,
  configuration LDAP externe, SAML2) est désormais un attribut de
  **chaque domaine** (`dns.domains[].authentication`), pas un réglage
  global de la plateforme --- conforme au fonctionnement réel de
  Carbonio. Les champs `authentication.methods`, `authentication.
  external_ldap` et `authentication.saml2` (niveau racine) ne sont plus
  lus. Jamais configurable sur un alias de domaine.
- **`authentication.native` remplacé par `authentication.
  password_policies`** (liste) : plusieurs politiques de mots de passe
  et de verrouillage peuvent désormais coexister, chacune avec une portée
  explicite (Plateforme, une COS précise, ou un domaine précis). Une
  seule entrée avec une portée "Plateforme" reproduit le comportement
  précédent (politique unique).
- **`authentication.connection.default_domain`** (nouveau) : domaine
  assumé lorsqu'un utilisateur se connecte sans préciser de domaine.
- Plusieurs serveurs LDAP externes par domaine, pour la répartition de
  charge et la haute disponibilité de l'annuaire (déjà supporté par la
  structure existante, confirmé explicitement pertinent dans ce nouveau
  contexte par domaine).
- Chapitre "Authentification" du DAT restructuré en conséquence :
  Connexion, Politiques de mots de passe (table avec portée), Protection
  anti brute-force, puis une sous-section par domaine (méthodes, LDAP
  externe, SAML2).

## 1.11.1 --- 2026-08-12

- **`client.carbonio_ce_version` supprimé** --- le tableau "Version
  déployée et documentation" affichait deux numéros de version distincts
  (un pour `product.version`, un second embarqué dans la ligne
  "Édition" pour la CE). La ligne "Édition" n'affiche plus désormais que
  le type d'édition ("Community Edition (CE)" / "Carbonio (Advanced)")
  --- `product.version` reste l'unique source du numéro de version,
  quelle que soit l'édition.

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
