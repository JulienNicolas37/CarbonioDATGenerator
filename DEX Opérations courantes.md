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

