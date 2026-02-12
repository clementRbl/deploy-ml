# 🔐 Configuration des Secrets et Variables

Ce document explique comment configurer les secrets et variables pour le pipeline CI/CD.

## 📋 Secrets GitHub requis

Dans votre repository GitHub, allez dans **Settings > Secrets and variables > Actions > Secrets** et ajoutez :

| Secret | Description | Exemple |
|--------|-------------|---------|
| `HF_TOKEN` | Token d'accès Hugging Face (Write) | `hf_xxxxxxxxxxxxxxx` |

## 📋 Variables GitHub requises

Dans **Settings > Secrets and variables > Actions > Variables** ajoutez :

| Variable | Description | Exemple |
|----------|-------------|---------|
| `HF_USERNAME` | Votre nom d'utilisateur HF | `mon-username` |
| `HF_SPACE_NAME` | Nom du Space à créer | `deploy-ml` |

### Obtenir un token Hugging Face

1. Connectez-vous sur [huggingface.co](https://huggingface.co)
2. Allez dans **Settings > Access Tokens**
3. Créez un nouveau token avec les permissions **Write**
4. Copiez le token et ajoutez-le comme secret GitHub

## 🌍 Environnements GitHub

Le pipeline utilise 3 environnements :

| Environnement | Branches | Description |
|--------------|----------|-------------|
| `development` | `feature/*` | Tests automatiques |
| `test` | Pull Requests | Tests + validation |
| `production` | `main` | Déploiement HF Spaces |

### Configurer l'environnement "production"

1. Dans GitHub, allez dans **Settings > Environments**
2. Créez un environnement nommé `production`
3. (Optionnel) Ajoutez des **Required reviewers** pour approuver les déploiements
4. (Optionnel) Ajoutez une **Wait timer** de X minutes

## 🚀 Créer un Hugging Face Space

1. Allez sur [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choisissez :
   - **Space name** : `deploy-ml` (ou autre)
   - **SDK** : `Docker` ou `Gradio`
   - **Visibility** : Public ou Private
3. Le pipeline CI/CD poussera automatiquement le code

## 📁 Variables d'environnement locales

Pour le développement local, copiez `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Puis modifiez les valeurs selon votre configuration.

## ⚠️ Sécurité

- **JAMAIS** commiter de secrets dans le code
- Utilisez toujours des variables d'environnement
- Le fichier `.env` est dans `.gitignore`
- Rotez régulièrement vos tokens
