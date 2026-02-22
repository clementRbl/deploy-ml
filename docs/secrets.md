# Gestion des secrets et variables d'environnement

Ce document décrit où et comment sont gérés les **secrets** et les **variables d'environnement** (local, CI/CD, déploiement).

---

## En local

- **Fichier utilisé** : `.env` à la racine du projet (créé à partir de `.env.example`).
- **Ne jamais commiter** : le fichier `.env` est listé dans `.gitignore`. Seul `.env.example` est versionné, avec des valeurs factices ou commentées.
- **Variables disponibles** (voir `.env.example`) :
  - `ENVIRONMENT` : `development` | `test` | `production`
  - `DEBUG` : `true` | `false`
  - `DATABASE_URL` : URL PostgreSQL (ex. `postgresql://user:pass@localhost:5432/deploy_ml`) — optionnel si les valeurs par défaut de `src/core/config.py` conviennent
  - `HF_TOKEN`, `HF_USERNAME`, `HF_SPACE_NAME` : utilisés uniquement si vous exécutez manuellement un script de déploiement vers Hugging Face (sinon gérés en CI)

**Bonnes pratiques** : copier `.env.example` vers `.env`, renseigner les vraies valeurs localement, ne jamais pousser `.env` sur le dépôt.

---

## En CI/CD (GitHub Actions)

Le workflow `.github/workflows/ci-cd.yml` utilise des **GitHub Secrets** pour tout ce qui est sensible :

| Secret | Rôle |
|--------|------|
| `GITHUB_TOKEN` | Fourni automatiquement par GitHub ; utilisé pour les commentaires de couverture sur les PR |
| `HF_TOKEN` | Token d'accès Hugging Face (Settings → Secrets and variables → Actions) |
| `HF_USERNAME` | Compte Hugging Face (ex. `clementrbl`) |
| `HF_SPACE_NAME` | Nom du Space (ex. `deploy-ml`) |

- Ces secrets ne sont **jamais** écrits en clair dans le workflow : on utilise `${{ secrets.HF_TOKEN }}`, etc.
- Le job **Deploy to Hugging Face** ne s’exécute que sur la branche `main` après un push ; il utilise `HF_TOKEN` pour l’upload via l’API Hugging Face Hub.

**Configuration** : dans le dépôt GitHub, aller dans *Settings → Secrets and variables → Actions* et ajouter `HF_TOKEN`, `HF_USERNAME`, `HF_SPACE_NAME` avec les valeurs réelles.

---

## Environnements (dev / test / prod)

| Environnement | Contexte | Comment |
|--------------|----------|--------|
| **Dev** | Développement local ou branches `feature/*` | Variable `ENVIRONMENT=development` (ou défaut). Base PostgreSQL locale, pas de déploiement. |
| **Test** | Pipeline CI (push ou PR sur `main` / `feature/**`) | Job `test` avec `ENVIRONMENT: test`. Pas d’accès à des secrets HF ; validation des métadonnées des modèles uniquement. |
| **Prod** | API déployée sur Hugging Face Spaces | Déclenché par un push sur `main`. Utilise `HF_TOKEN`, `HF_USERNAME`, `HF_SPACE_NAME` pour uploader le code et déclencher le build Docker sur HF. |

La base de données PostgreSQL n’est **pas** exposée en production (déploiement HF = API seule). Les secrets de connexion DB restent en local.

---

## Résumé

- **Local** : `.env` (non versionné), copié depuis `.env.example`.
- **CI** : GitHub Secrets pour Hugging Face ; pas de clés en clair dans le workflow.
- **Prod** : identifiants HF fournis par les secrets au moment du déploiement.

Pour plus d’informations sur la sécurisation de l’API (CORS, authentification), voir la section [Sécurisation](../README.md#sécurisation) du README.
