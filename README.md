# digital-marketing-campaign-analysis
Marketing Campaign Analytics

An end-to-end marketing analytics platform that cleans campaign data, visualizes performance, trains machine learning models to predict customer conversion, generates downloadable reports, and serves everything through a role-gated web application.

Built as a full data science + web engineering project — from raw CSV to a secured, multi-role Django app, running locally.

What it does
Cleans and validates an uploaded customer/campaign dataset (missing values, duplicates, outliers — checked and logged)
Generates interactive dashboards (conversion distribution, conversion rate by channel, engagement metrics) using Chart.js
Trains and compares four ML models — Logistic Regression, Decision Tree, Random Forest, and Gradient Boosting — for two tasks:
Classification: will this customer convert? (Yes/No)
Regression: what is their expected conversion rate?
Runs live predictions on new or hypothetical customer/campaign data through a web form
Auto-generates prediction reports as downloadable PDF (CSV/Excel also supported)
Role-based access for Admin, Manager, and Client — each sees a different, appropriately scoped view of the data
Tech stack
Purpose	Tools
Backend framework	Django
Data cleaning & analysis	Pandas, NumPy
Machine learning	Scikit-learn (Logistic Regression, Decision Tree, Random Forest, Gradient Boosting)
Model persistence	joblib
Dashboard charts	Chart.js
Report generation	ReportLab (PDF), openpyxl (Excel), Pandas (CSV)
Styling	Bootstrap 5
Notebook/EDA environment	Jupyter (via VS Code extension)
Dataset

digital_marketing_campaign_dataset.csv — 8,000 customer records with 20 features:

CustomerID, Age, Gender, Income, CampaignChannel, CampaignType, AdSpend,
ClickThroughRate, ConversionRate, WebsiteVisits, PagesPerVisit, TimeOnSite,
SocialShares, EmailOpens, EmailClicks, PreviousPurchases, LoyaltyPoints,
AdvertisingPlatform, AdvertisingTool, Conversion

Data quality notes:

No missing values, no duplicate rows, no meaningful outliers found
AdvertisingPlatform and AdvertisingTool contain a single constant value across all records and were excluded from modeling — they carry no predictive information
Conversion is imbalanced (~87.65% converted vs 12.35% not) — handled during model training with class_weight='balanced'
Machine learning results
Classification (predicting Conversion)
Model	Accuracy	Precision	Recall	F1
Logistic Regression	73.3%	94.8%	73.5%	0.828
Decision Tree	82.1%	90.0%	89.5%	0.898
Random Forest	90.6%	91.9%	97.9%	0.948
Gradient Boosting	91.0%	91.2%	99.3%	0.951

Gradient Boosting performs best overall; Logistic Regression is notably better at catching non-converting customers specifically.
Regression (predicting exact ConversionRate)
Model	RMSE	R²
Linear Regression	0.054	-0.002
Decision Tree	0.079	-1.13 (overfit)
Random Forest	0.055	-0.032
Gradient Boosting	0.054	-0.017

None of the regressors meaningfully outperform a naive baseline (R² ≈ 0 across all four). This is a genuine finding, not a modeling failure — see below.

Key findings
No single feature strongly predicts conversion. The strongest individual correlation (TimeOnSite) was only 0.13. Pairwise interaction effects between top features were also tested and found no meaningful combined effect (max |r| = 0.018) — ruling out the possibility that predictive signal was hiding in feature combinations.
Ad spend does not correlate with conversion rate (r ≈ -0.02) — spending more does not predict higher conversion in this dataset.
Classification succeeds where regression fails. The available features are sufficient to distinguish converters from non-converters as a category, but not precise enough to predict the exact conversion rate as a number — suggesting conversion rate is influenced by factors not captured in this dataset (e.g. ad creative quality, timing, seasonality).
High overall accuracy can hide poor minority-class performance. Gradient Boosting's strong headline numbers come largely from how well it identifies the majority (converting) class; it only catches ~32% of actual non-converters. Logistic Regression, despite lower overall accuracy, catches non-converters more reliably (~72%) — a meaningful tradeoff depending on whether the business goal is overall accuracy or targeted retention.
Application structure
Workflow
Upload → Clean → Explore → Train models → Predict → Report → Role-gated views
