# Plan Professionnel — Pipeline Business Analytics & Prévision de la Demande
## Dataset : Olist Brazilian E-Commerce

---

## 1. Vue d'ensemble

**Objectif** : Construire un pipeline end-to-end (ingestion → transformation → analyse → modeling) sur des données e-commerce réelles, démontrant des compétences en Data Engineering, Data Analysis et Machine Learning dans un seul repo cohérent.

**Dataset** : Olist Brazilian E-Commerce (Kaggle: `olistbr/brazilian-ecommerce`)
- 100 000 commandes réelles, anonymisées (2016-2018)
- 9 fichiers CSV relationnels : orders, customers, order_items, products, payments, reviews, sellers, geolocation, category_translation
- Données commerciales réelles → crédibilité forte auprès des recruteurs

---

## 2. Architecture technique

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌─────────────┐
│  Ingestion   │──▶│ Transformation│──▶│  Data Warehouse│──▶│  Analyse/BI │
│  (Python)    │   │    (dbt)      │   │   (DuckDB/PG)  │   │ (Streamlit) │
└─────────────┘   └──────────────┘   └───────────────┘   └─────────────┘
                                              │
                                              ▼
                                     ┌───────────────┐
                                     │   Modeling     │
                                     │ (Forecast + RFM)│
                                     └───────────────┘
                                              │
                                              ▼
                                     ┌───────────────┐
                                     │  API (FastAPI) │
                                     └───────────────┘
```

---

## 3. Stack technique

| Couche | Outil | Justification |
|---|---|---|
| Ingestion | Python (pandas, requests) | Simple, standard |
| Orchestration | Airflow (ou cron simplifié si contrainte de temps) | Mot-clé très recherché |
| Transformation | dbt-core | Standard industrie pour ELT |
| Warehouse | DuckDB (local) ou PostgreSQL | Gratuit, performant, pas besoin de cloud payant |
| BI/Dashboard | Streamlit | Rapide à déployer, personnalisable |
| Modeling | Prophet + PyTorch (LSTM) | Baseline + modèle avancé |
| Serving | FastAPI | Expose les prédictions via API |
| Conteneurisation | Docker + docker-compose | Reproductibilité, très valorisé |
| Versioning | Git/GitHub | Obligatoire |

---

## 4. Roadmap détaillée (6 semaines)

### Semaine 1 — Setup & Ingestion
- Télécharger le dataset Olist, l'explorer (EDA rapide)
- Écrire les scripts d'ingestion Python (lecture CSV → validation schéma → écriture Parquet)
- Mettre en place le repo Git avec structure de dossiers propre
- Livrable : scripts d'ingestion fonctionnels + README initial

### Semaine 2 — Modélisation des données & dbt
- Concevoir un schéma en étoile : `fact_orders`, `dim_customer`, `dim_product`, `dim_date`, `dim_seller`
- Écrire les modèles dbt (staging → intermediate → marts)
- Ajouter des tests dbt (unicité, non-null, relations)
- Livrable : modèles dbt documentés + `dbt docs generate`

### Semaine 3 — Orchestration
- Créer un DAG Airflow : extract → load → dbt run → dbt test
- Gérer les erreurs, logs, retries
- Dockeriser Airflow + warehouse
- Livrable : pipeline orchestré reproductible via `docker-compose up`

### Semaine 4 — Analyse & Dashboard
- KPIs business : CA par catégorie/région/mois, délai de livraison moyen, taux de satisfaction (reviews), top vendeurs
- Segmentation client RFM (Récence, Fréquence, Montant) + clustering (K-Means)
- Dashboard Streamlit interactif (filtres par période/région/catégorie)
- Livrable : dashboard déployé (Streamlit Cloud, gratuit)

### Semaine 5 — Modeling (Prévision de la demande)
- Agrégation des ventes par catégorie/semaine
- Baseline : Prophet (rapide, interprétable)
- Modèle avancé : LSTM ou petit Transformer (réutilise ta logique de séries temporelles)
- Backtesting rigoureux : validation walk-forward (train sur passé, test sur futur — jamais de fuite de données)
- Métriques : MAE, RMSE, MAPE — comparaison baseline vs modèle avancé
- Livrable : notebook de modeling + rapport de performance

### Semaine 6 — Packaging & Documentation
- API FastAPI qui sert les prédictions du modèle
- README complet avec architecture, instructions d'installation, captures d'écran
- Article technique (Medium/LinkedIn) expliquant les choix techniques
- Nettoyage du repo, CI basique (GitHub Actions : lint + tests)

---

## 5. Structure de repo recommandée

```
business-analytics-pipeline/
├── ingestion/
│   ├── extract.py
│   └── load.py
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── tests/
│   └── dbt_project.yml
├── orchestration/
│   └── dags/
│       └── pipeline_dag.py
├── dashboard/
│   └── app.py
├── modeling/
│   ├── rfm_segmentation.ipynb
│   ├── demand_forecasting.ipynb
│   └── model_evaluation.py
├── api/
│   └── main.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 6. Ce qui différencie ce projet des projets Kaggle classiques

1. **Pipeline complet** vs notebook isolé — montre une compréhension du cycle de vie de la donnée
2. **Tests de qualité de données** (dbt tests) — rigueur rarement vue dans les portfolios juniors
3. **Backtesting temporel correct** — évite la fuite de données, erreur très fréquente
4. **Reproductibilité totale** via Docker — un recruteur peut cloner et lancer en une commande
5. **Double valeur business** : segmentation client + prévision de demande — pas juste un modèle isolé

---

## 7. Présentation pour le portfolio

- README avec diagramme d'architecture (peut être fait avec draw.io ou mermaid)
- Capture d'écran du dashboard en haut du README
- Section "Résultats clés" avec chiffres concrets (ex: "Modèle LSTM réduit le MAPE de X% vs baseline Prophet")
- Lien vers dashboard déployé (Streamlit Cloud) pour que les recruteurs puissent interagir sans setup
- Article de blog en complément (démontre la capacité à communiquer, compétence sous-estimée)

---

## 8. Prochaines étapes immédiates

1. Télécharger le dataset Olist et faire un EDA rapide (1-2 jours)
2. Définir précisément le schéma en étoile
3. Commencer les scripts d'ingestion
