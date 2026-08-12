# Référentiel des opérations Carbonio

Ce document recense les principales opérations de maintenance et d'exploitation
courante d'une infrastructure Zextras Carbonio.

Les opérations sont organisées par brique fonctionnelle afin de pouvoir être
utilisées comme référentiel pour la génération d'un DAT, d'un dossier
d'exploitation ou d'un plan de maintenance.

---

# 1. Opérations de maintenance MCO / MCS

## 1.1 MTA IN

### Supervision et contrôle
- Vérification de l'état des services SMTP/Postfix
- Contrôle des files d'attente entrantes
- Identification des messages bloqués ou différés
- Analyse des erreurs SMTP et codes de rejet
- Contrôle des volumes de messages entrants
- Détection des variations anormales de trafic
- Vérification des connexions avec la passerelle antispam/antivirus
- Contrôle de la distribution vers les Mailstores
- Analyse des logs MTA

### Maintenance
- Purge contrôlée des messages définitivement bloqués
- Relance / requeue de messages
- Mise à jour des règles de routage
- Mise à jour des domaines acceptés
- Vérification des DNS et MX
- Vérification des certificats TLS
- Contrôle des versions et protocoles TLS autorisés
- Test SMTP entrant après modification

### Sécurité
- Analyse des tentatives de relay
- Contrôle des restrictions SMTP
- Vérification SPF
- Vérification DKIM
- Vérification DMARC
- Analyse des pics de connexions
- Analyse des comportements SMTP suspects

---

## 1.2 MTA OUT

### Supervision
- Contrôle de la file d'attente sortante
- Analyse des messages deferred
- Analyse des messages bounced
- Surveillance du volume de messages sortants
- Détection d'un compte générant un volume anormal
- Détection d'un domaine générant un volume anormal
- Vérification de la connectivité Internet
- Vérification de la connectivité avec le Smart Host
- Analyse des rejets des plateformes distantes

### Maintenance
- Requeue des messages
- Purge contrôlée des files
- Modification du routage SMTP
- Gestion des Smart Hosts
- Vérification des IP publiques
- Vérification des mécanismes NAT
- Contrôle des PTR
- Vérification SPF
- Vérification DKIM
- Vérification DMARC
- Contrôle des certificats TLS
- Tests SMTP sortants

### Réputation et sécurité
- Surveillance des RBL / listes de blocage
- Analyse des problèmes de réputation IP
- Investigation en cas de spam sortant
- Identification des comptes compromis
- Blocage temporaire d'un compte compromis
- Adaptation des limites de débit

---

## 1.3 MTA AUTH

### Exploitation
- Vérification du service SMTP Submission
- Contrôle des ports 587 / 465 selon architecture
- Contrôle de l'authentification SMTP
- Vérification du dialogue avec LDAP
- Analyse des échecs d'authentification
- Vérification du routage vers le MTA OUT

### Sécurité
- Détection des attaques brute-force
- Identification des comptes compromis
- Contrôle des volumes par utilisateur
- Contrôle des mécanismes SASL
- Vérification des politiques TLS
- Révocation ou blocage des comptes compromis

---

## 1.4 LDAP / Directory

### Supervision
- Vérification de la disponibilité LDAP
- Vérification des ports LDAP / LDAPS
- Contrôle de la réplication entre nœuds
- Surveillance du replication lag
- Contrôle de la cohérence Master / Replica
- Surveillance CPU
- Surveillance RAM
- Surveillance disque
- Surveillance de la taille de la base LDAP
- Analyse des logs LDAP

### Maintenance
- Vérification périodique de la réplication
- Reconstruction / réindexation lorsque nécessaire
- Sauvegarde LDAP
- Test de restauration
- Vérification de la cohérence des données
- Gestion des certificats LDAP
- Nettoyage des anciennes données et logs

---

## 1.5 MAILSTORE

### Services
- Vérification de l'état des services Mailstore
- Contrôle des processus Java
- Surveillance JVM
- Contrôle Heap
- Contrôle Garbage Collector
- Analyse des logs applicatifs
- Contrôle des threads
- Surveillance des temps de réponse

### Stockage
- Surveillance de l'espace disque
- Surveillance des volumes primaires
- Surveillance des volumes secondaires
- Contrôle des volumes d'index
- Contrôle des volumes Blob
- Vérification des montages
- Vérification de l'accès au stockage objet / S3
- Surveillance de la croissance des données
- Contrôle des IOPS
- Contrôle des latences disque

### Mailbox
- Contrôle de la cohérence des Mailboxes
- Analyse des Mailboxes anormalement volumineuses
- Vérification des quotas
- Réindexation d'une Mailbox
- Reconstruction d'index
- Analyse des erreurs de Blob
- Investigation des messages manquants ou corrompus
- Purge conformément aux politiques de rétention

### Maintenance
- Redémarrage contrôlé des services
- Nettoyage des logs
- Gestion des caches
- Maintenance des index
- Vérification de la cohérence DB / Blob / Index
- Contrôle des sauvegardes
- Test de restauration d'une Mailbox

---

## 1.6 PROXY

### Supervision
- Vérification de Nginx / Proxy
- Contrôle HTTP / HTTPS
- Contrôle IMAP / IMAPS
- Contrôle POP / POPS si utilisés
- Contrôle des connexions vers les Mailstores
- Analyse des erreurs HTTP 4xx
- Analyse des erreurs HTTP 5xx
- Surveillance des connexions simultanées
- Surveillance CPU / RAM / réseau

### Maintenance
- Mise à jour de configuration Proxy
- Reload contrôlé
- Restart contrôlé
- Gestion des certificats HTTPS
- Modification des timeouts
- Modification des limites de connexions
- Gestion des règles de Reverse Proxy
- Test Webmail après modification
- Test API après modification
- Test EAS après modification
- Test IMAP après modification

### Sécurité
- Analyse des tentatives de brute-force
- Contrôle des protocoles TLS
- Contrôle des Cipher Suites
- Analyse des connexions anormales
- Blocage éventuel d'IP ou User-Agent

---

## 1.7 PostgreSQL

### Supervision
- Vérification de l'état PostgreSQL
- Surveillance CPU / RAM
- Surveillance de l'espace disque
- Surveillance de la croissance des bases
- Contrôle du nombre de connexions
- Recherche des connexions bloquées
- Recherche des requêtes longues
- Contrôle des locks
- Surveillance des WAL
- Analyse des logs PostgreSQL

### Réplication / HA
- Vérification de la réplication
- Surveillance du replication lag
- Vérification de l'état des replicas
- Contrôle de la génération des WAL
- Contrôle de la conservation des WAL
- Vérification de la capacité de failover

### Maintenance
- Contrôle VACUUM / Autovacuum
- ANALYZE
- REINDEX lorsque nécessaire
- Gestion des statistiques
- Rotation des logs
- Sauvegarde PostgreSQL
- Test de restauration
- Contrôle de l'intégrité des sauvegardes

---

## 1.8 Redis

- Vérification de la disponibilité
- Contrôle de la consommation mémoire
- Surveillance du nombre de connexions
- Surveillance des clés
- Surveillance des expirations
- Contrôle des erreurs et timeouts
- Contrôle de la réplication
- Contrôle des mécanismes de persistance
- Vérification de la configuration mémoire
- Redémarrage contrôlé

---

## 1.9 Carbonio Mesh

- Vérification de l'état du cluster Mesh
- Contrôle des membres
- Vérification du quorum
- Vérification de l'enregistrement des services
- Contrôle des services indisponibles
- Vérification des communications inter-nœuds
- Analyse des logs
- Réintégration d'un nœud
- Redémarrage contrôlé
- Contrôle des communications sécurisées

---

## 1.10 Backup

### Exploitation
- Vérification quotidienne des sauvegardes
- Contrôle des erreurs
- Vérification de l'espace disponible
- Surveillance de la durée des sauvegardes
- Contrôle des sauvegardes incrémentales
- Vérification du stockage de destination
- Vérification de l'accès S3

### Maintenance
- Test de restauration d'un message
- Test de restauration d'une Mailbox
- Test de restauration d'un compte supprimé
- Test de restauration après sinistre
- Vérification périodique de l'intégrité
- Contrôle de la politique de rétention
- Purge des sauvegardes expirées

---

## 1.11 Système d'exploitation

- Surveillance CPU
- Surveillance RAM
- Surveillance Swap
- Surveillance Filesystem
- Surveillance Inodes
- Surveillance I/O
- Surveillance réseau
- Vérification NTP / Chrony
- Contrôle DNS
- Rotation des logs
- Nettoyage des fichiers temporaires
- Installation des mises à jour de sécurité
- Gestion des CVE
- Contrôle des services Systemd
- Contrôle des erreurs Kernel
- Vérification des montages
- Contrôle des certificats système
- Contrôle des règles Firewall
- Contrôle SSH
- Vérification des comptes système
- Vérification des droits sudo

---

## 1.12 Certificats / PKI

- Inventaire des certificats
- Surveillance des dates d'expiration
- Renouvellement des certificats
- Déploiement des certificats
- Vérification de la chaîne de certification
- Vérification des SAN
- Contrôle des clés privées
- Vérification des certificats Proxy
- Vérification des certificats MTA
- Vérification des certificats LDAP
- Vérification des certificats des services internes
- Tests TLS après renouvellement

---

## 1.13 DNS

- Vérification des enregistrements MX
- Vérification des enregistrements A
- Vérification des enregistrements AAAA
- Vérification des PTR
- Vérification SPF
- Vérification DKIM
- Vérification DMARC
- Vérification des enregistrements de découverte
- Contrôle des TTL
- Tests de résolution depuis les différents nœuds
- Contrôle de cohérence DNS interne / externe

---

## 1.14 Maintenance globale Carbonio

- Contrôle de la version installée
- Analyse des Release Notes
- Analyse des prérequis avant Upgrade
- Vérification des dépendances entre composants
- Sauvegarde avant Upgrade
- Mise à jour Carbonio
- Contrôle Post-Upgrade
- Vérification des migrations de schéma
- Tests fonctionnels Webmail
- Tests SMTP IN
- Tests SMTP OUT
- Tests SMTP AUTH
- Tests IMAP
- Tests LDAP
- Tests API
- Tests Mobile / EAS
- Contrôle des logs après Upgrade
- Validation du retour au nominal
- Mise à jour du DAT
- Mise à jour du dossier d'exploitation

---

# 2. Opérations courantes d'exploitation

## 2.1 DOMAIN

### Gestion des domaines
- Création d'un domaine
- Suppression d'un domaine
- Modification d'un domaine
- Renommage d'un domaine
- Création d'un alias de domaine
- Suppression d'un alias de domaine
- Définition du domaine par défaut
- Configuration du routage d'un domaine
- Configuration d'un Split Domain
- Modification du COS par défaut
- Configuration des quotas par défaut
- Activation / désactivation de fonctionnalités
- Configuration de l'authentification du domaine
- Configuration LDAP externe
- Configuration SAML / SSO
- Modification des paramètres de sécurité
- Activation / configuration de la 2FA
- Configuration DKIM
- Génération d'une clé DKIM
- Rotation d'une clé DKIM
- Export de la configuration d'un domaine
- Consultation des statistiques du domaine

---

## 2.2 ACCOUNT

### Cycle de vie
- Création d'un compte
- Modification d'un compte
- Suppression d'un compte
- Suspension d'un compte
- Réactivation d'un compte
- Verrouillage d'un compte
- Déverrouillage d'un compte
- Changement d'adresse principale
- Renommage d'un compte
- Modification du COS
- Consultation de l'état du compte

### Authentification
- Réinitialisation du mot de passe
- Forçage du changement de mot de passe
- Déverrouillage après échecs d'authentification
- Activation de la 2FA
- Désactivation de la 2FA
- Réinitialisation de la 2FA
- Révocation des sessions utilisateur
- Révocation des mots de passe applicatifs
- Contrôle des dernières connexions

### Adresses
- Ajout d'un alias
- Suppression d'un alias
- Modification de l'adresse principale
- Configuration d'une adresse de transfert
- Suppression d'un transfert
- Configuration de la conservation d'une copie locale

### Quotas
- Consultation du quota
- Modification du quota
- Identification des comptes dépassant un seuil
- Augmentation temporaire du quota
- Analyse de l'occupation d'une Mailbox

---

## 2.3 MAILSTORE / MAILBOX

- Consultation de la localisation d'une Mailbox
- Consultation de la taille d'une Mailbox
- Déplacement d'une Mailbox entre Mailstores
- Réindexation d'une Mailbox
- Vérification d'une Mailbox
- Réparation d'une Mailbox
- Purge d'éléments
- Purge de la corbeille
- Purge des éléments supprimés
- Recherche administrative de messages
- Export d'une Mailbox
- Import d'une Mailbox
- Restauration d'un message
- Restauration d'un dossier
- Restauration d'une Mailbox
- Restauration d'un compte supprimé
- Consultation des informations techniques d'une Mailbox
- Analyse d'une Mailbox présentant des erreurs
- Gestion des volumes associés

---

## 2.4 LISTES DE DISTRIBUTION

- Création d'une liste de distribution
- Suppression d'une liste
- Renommage d'une liste
- Ajout d'un membre
- Suppression d'un membre
- Ajout en masse de membres
- Suppression en masse de membres
- Export des membres
- Modification des propriétaires
- Gestion des droits d'envoi
- Restriction aux membres
- Autorisation d'expéditeurs externes
- Gestion des listes imbriquées
- Ajout d'un alias
- Suppression d'un alias
- Recherche des listes auxquelles appartient un utilisateur

---

## 2.5 GROUPES DYNAMIQUES

- Création d'un groupe dynamique
- Suppression d'un groupe dynamique
- Modification d'un groupe dynamique
- Définition des critères d'appartenance
- Modification des critères d'appartenance
- Vérification des membres résultants
- Gestion des droits associés
- Gestion des propriétaires
- Gestion des alias

---

## 2.6 COS

- Création d'un COS
- Duplication d'un COS
- Modification d'un COS
- Suppression d'un COS
- Affectation d'un COS à un utilisateur
- Affectation en masse d'un COS
- Modification du COS par défaut d'un domaine
- Modification des quotas
- Activation / désactivation de fonctionnalités
- Paramétrage POP / IMAP
- Paramétrage des fonctions collaboratives
- Paramétrage Mobile / EAS
- Configuration des politiques de mot de passe
- Configuration des politiques de session
- Comparaison de deux COS
- Identification des comptes associés à un COS

---

## 2.7 MTA IN

- Ajout d'un domaine accepté
- Suppression d'un domaine accepté
- Modification du routage entrant
- Création d'une route SMTP spécifique
- Modification d'une route SMTP
- Vérification d'un flux entrant
- Recherche d'un message dans les logs
- Recherche par Message-ID
- Recherche par expéditeur
- Recherche par destinataire
- Analyse d'un rejet SMTP
- Analyse d'un message différé
- Requeue d'un message
- Suppression d'un message de la queue
- Purge contrôlée d'une queue
- Blocage d'une adresse
- Déblocage d'une adresse
- Blocage d'un domaine
- Déblocage d'un domaine
- Test SMTP entrant
- Vérification du routage vers une Mailbox

---

## 2.8 MTA OUT

- Configuration d'un Smart Host
- Modification du routage sortant
- Création d'une exception de routage
- Recherche d'un message sortant
- Analyse d'un Bounce
- Analyse d'un Deferred
- Requeue d'un message
- Suppression d'un message
- Purge contrôlée d'une queue
- Test d'envoi vers Internet
- Test vers un domaine spécifique
- Analyse d'un rejet distant
- Analyse SPF
- Analyse DKIM
- Rotation d'une clé DKIM
- Analyse DMARC
- Investigation d'un problème de réputation
- Blocage temporaire d'un expéditeur compromis

---

## 2.9 MTA AUTH

- Test d'authentification SMTP
- Activation de la soumission authentifiée
- Désactivation de la soumission authentifiée
- Diagnostic d'un échec SMTP AUTH
- Déblocage d'un utilisateur
- Révocation d'accès
- Recherche des connexions d'un utilisateur
- Recherche par IP source
- Analyse d'un comportement suspect
- Blocage d'une IP
- Déblocage d'une IP
- Modification des restrictions de soumission
- Test TLS / STARTTLS

---

## 2.10 LDAP / DIRECTORY

- Recherche d'un objet LDAP
- Consultation des attributs d'un compte
- Modification d'un attribut
- Recherche d'un domaine
- Recherche d'un alias
- Recherche d'une liste de distribution
- Recherche d'un COS
- Vérification de l'existence d'un objet
- Export d'informations LDAP
- Vérification de la réplication d'une modification
- Gestion des comptes administrateurs
- Création d'un administrateur délégué
- Modification des droits administratifs
- Suppression des droits administratifs

---

## 2.11 PROXY

- Ajout d'un certificat
- Modification d'un certificat
- Renouvellement d'un certificat
- Vérification de la chaîne TLS
- Modification de la configuration HTTPS
- Modification de la configuration IMAP / IMAPS
- Modification des timeouts
- Modification des limites de connexion
- Ajout d'une règle spécifique
- Blocage d'une IP
- Déblocage d'une IP
- Diagnostic d'une erreur HTTP 4xx
- Diagnostic d'une erreur HTTP 5xx
- Diagnostic d'un problème Webmail
- Diagnostic d'un problème IMAP
- Diagnostic d'un problème EAS
- Test d'accès à un Mailstore depuis le Proxy

---

## 2.12 POSTGRESQL

- Consultation de l'état des bases
- Consultation des connexions
- Recherche des requêtes longues
- Analyse d'un Lock
- Terminaison contrôlée d'une session
- Vérification de la réplication
- Vérification de la volumétrie
- Sauvegarde
- Restauration
- Vérification d'une sauvegarde
- Analyse d'une erreur applicative liée à PostgreSQL
- VACUUM / ANALYZE exceptionnel
- REINDEX lorsque nécessaire

> La modification manuelle des données applicatives Carbonio directement
> dans PostgreSQL ne doit pas être considérée comme une opération courante
> d'exploitation. Elle doit faire l'objet d'une procédure spécifique et
> validée.

---

## 2.13 REDIS

- Vérification de disponibilité
- Consultation des connexions
- Analyse d'une saturation mémoire
- Analyse des Timeouts
- Redémarrage contrôlé
- Vérification de la réplication

---

## 2.14 MESH

- Consultation des membres
- Vérification de l'état des services
- Vérification du quorum
- Diagnostic d'un service non enregistré
- Réintégration d'un nœud
- Redémarrage contrôlé d'un composant
- Vérification des communications interservices

---

## 2.15 BACKUP / RESTORE

- Recherche d'un élément sauvegardé
- Restauration d'un message
- Restauration d'un dossier
- Restauration d'une Mailbox
- Restauration d'un compte
- Restauration d'un compte supprimé
- Restauration de plusieurs comptes
- Restauration vers un compte alternatif
- Export avant suppression
- Vérification de la présence d'une sauvegarde
- Modification de la rétention
- Purge d'anciennes sauvegardes
- Test périodique de restauration

---

## 2.16 ADMINISTRATION / DÉLÉGATION

- Création d'un administrateur global
- Création d'un administrateur délégué
- Suppression d'un administrateur
- Modification des droits
- Attribution de droits sur un domaine
- Attribution de droits sur certaines opérations
- Révocation des droits
- Audit des administrateurs
- Contrôle des actions administratives
- Rotation des credentials administratifs
- Réinitialisation des credentials administratifs

---

## 2.17 OPÉRATIONS EN MASSE

- Création en masse de comptes
- Suppression en masse de comptes
- Suspension en masse de comptes
- Réactivation en masse de comptes
- Modification de COS en masse
- Modification de quotas en masse
- Ajout d'alias en masse
- Suppression d'alias en masse
- Ajout de membres à une liste de distribution en masse
- Suppression de membres d'une liste en masse
- Modification d'attributs en masse
- Import CSV
- Export CSV
- Réinitialisation de mots de passe en masse
- Migration de Mailboxes en masse
- Déplacement de Mailboxes en masse
- Extraction d'informations sur une population
- Application d'une configuration à tous les comptes d'un domaine

---

# 3. Classification recommandée des opérations

Chaque opération peut être associée à une catégorie.

## EXPLOITATION
Opération fonctionnelle courante réalisée dans le cadre de l'administration
normale de la plateforme.

Exemples :
- Création d'un compte
- Réinitialisation d'un mot de passe
- Création d'une liste de distribution

## MAINTENANCE_PREVENTIVE
Opération réalisée périodiquement afin de prévenir une dégradation ou
un incident.

Exemples :
- Vérification de la réplication LDAP
- Contrôle de l'espace disque
- Vérification des sauvegardes

## MAINTENANCE_CORRECTIVE
Opération réalisée à la suite d'une anomalie ou d'un incident.

Exemples :
- Réindexation d'une Mailbox
- Requeue d'un message
- Réintégration d'un nœud Mesh

## MAINTENANCE_EVOLUTIVE
Opération modifiant ou faisant évoluer la plateforme.

Exemples :
- Upgrade Carbonio
- Modification d'architecture
- Ajout d'un Mailstore

## SECURITE
Opération relative au maintien en condition de sécurité.

Exemples :
- Rotation d'une clé DKIM
- Renouvellement d'un certificat
- Installation d'un correctif de sécurité
- Blocage d'un compte compromis

---

# 4. Métadonnées recommandées pour une opération

Chaque opération du référentiel peut être décrite avec les attributs suivants :

- `id`
- `name`
- `description`
- `component`
- `category`
- `trigger`
- `frequency`
- `criticality`
- `user_impact`
- `service_interruption`
- `automation`
- `interfaces`
- `prerequisites`
- `pre_checks`
- `procedure`
- `post_checks`
- `rollback`
- `traceability`
- `required_skill_level`
- `estimated_duration`

Exemple :

| Attribut | Valeur |
|---|---|
| ID | `ACCOUNT_PASSWORD_RESET` |
| Nom | Réinitialisation du mot de passe |
| Brique | ACCOUNT |
| Catégorie | EXPLOITATION |
| Déclenchement | À la demande |
| Fréquence | Ponctuelle |
| Criticité | Faible |
| Impact utilisateur | Oui |
| Interruption | Non |
| Automatisable | Oui |
| Interfaces | CLI / ZAP / API |
| Prérequis | Droits administrateur |
| Contrôle avant | Vérification du compte |
| Contrôle après | Validation de l'authentification |
| Rollback | N/A |
| Traçabilité | Ticket / Audit |
| Niveau | N1 / N2 |
| Durée indicative | 5 minutes |
