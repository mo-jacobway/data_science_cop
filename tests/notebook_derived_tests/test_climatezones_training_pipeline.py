"""ClimateZones Training Pipeline - Environment Validation Test

This script's workflow content originated from the ClimateZones Training Pipeline
tutorial notebook and was reduced to provide a representative environment-
validation workflow.

The workflow content below remains substantially derived from that reduced
workflow and is executed within the environment-validation framework.

Test framework functionality including validation reporting, exception handling,
provenance capture and artefact retention is provided separately by
test_framework_utils.py.

* Author: Stephen Haddad; Environment-validation test wrapper and workflow reduction: Jacob Way;
* Affiliation: UK Met Office
* History: 1.0
* Last update: 2026-09-15
* (c) British Crown Copyright 2017-2026, Met Office. Please see LICENSE.md for license details.

Running this test
-----------------
This script forms part of an environment-validation framework and contains
the workflow-specific implementation of the ClimateZones Training Pipeline
validation test.

It is intended to be executed via:

    run_test.sh --test climatezones_training_pipeline [--module <module>] [--retention] [--log-level <level>]

which loads the environment under test and invokes this workflow through
the framework.

Data statement
--------------
This script is an environment-validation implementation based on the original
ClimateZones Training Pipeline tutorial workflow.

The underlying data referenced by the workflow is the Koppen-Geiger Climate
Classification dataset created by GloH2O.

References
----------
- Climate Zones Dataset:
  https://www.gloh2o.org/koppen/#:~:text=The%20K%C3%B6ppen%2DGeiger%20climate%20classification%20maps%20are%20high%2Dresolution,Climate%20Sensitivity%20(ECS)%2C%20and%20historical%20warming%20trend
"""

import pathlib
import os
import json

import pandas

import matplotlib
import matplotlib.pyplot

import sklearn
import sklearn.preprocessing
import sklearn.tree

import pickle

import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
import test_framework_utils as test_framework

# ---------------------------------------------------------------------
# Notebook workflow helpers
# ---------------------------------------------------------------------

def get_platform_dir(select_platform, config):
    try:
        root_path = pathlib.Path(config['default_dirs'][select_platform]) / 'climate_zones'
    except KeyError:
        root_path = pathlib.Path(os.environ['HOME']) / 'climate_zones'
    return root_path

# ---------------------------------------------------------------------
# Notebook derived workflow
# ---------------------------------------------------------------------

def run_notebook_derived_workflow():
    CONFIG_PATH = (test_framework.DATA_SCIENCE_COP_ROOT / "ml_examples" / "climate_zones" / "config.json")

    with open(CONFIG_PATH, "r") as tutorial_config_file:
        tutorial_config = json.load(tutorial_config_file)

    resolutions_dict = {float(k1): v1 for k1, v1 in tutorial_config['resolutions_names'].items()}
    ml_ready_fname_template = tutorial_config['csv_out_template']
    current_platform = tutorial_config['platform']
    random_seed = tutorial_config['random_seed']

    root_data_dir = get_platform_dir(current_platform, tutorial_config)
    ml_ready_dir = root_data_dir / 'ml_ready'

    current_res = 1.0
    mlready_data_path = ml_ready_dir / ml_ready_fname_template.format(resolution=resolutions_dict[current_res])
    zones_df = pandas.read_csv(mlready_data_path)

    predictors_dict = {
        'precip_mean': [c1 for c1 in zones_df.columns if 'precipitation' in c1 and 'mean' in c1],
        'precip_std': [c1 for c1 in zones_df.columns if 'precipitation' in c1 and 'std' in c1],
        'temp_mean': [c1 for c1 in zones_df.columns if 'air_temperature' in c1 and 'mean' in c1],
        'temp_std': [c1 for c1 in zones_df.columns if 'air_temperature' in c1 and 'std' in c1],
    }

    predictors = predictors_dict['precip_mean'] + predictors_dict['temp_mean']
    target_var = 'climate_group'

    test_frac = 0.1
    held_out_df = zones_df.groupby(['period_start','scenario']).sample(frac=test_frac, random_state=random_seed)
    train_df = zones_df.drop(held_out_df.index)

    train_df[predictors].describe()

    input_scaler = sklearn.preprocessing.StandardScaler()
    input_scaler.fit(train_df[predictors])
    X_train = input_scaler.transform(train_df[predictors])

    target_encoder = sklearn.preprocessing.LabelEncoder()
    target_encoder.fit(train_df[[target_var]])
    y_train = target_encoder.transform(train_df[[target_var]])

    classifiers_params = {
        'decision_tree': {'class': sklearn.tree.DecisionTreeClassifier, 'opts': {'max_depth': 10, 'class_weight': 'balanced'}},
        'random_forest': {'class': sklearn.ensemble.RandomForestClassifier, 'opts': {'max_depth': 10, 'class_weight': 'balanced', 'n_estimators': 10}},
        'ann_3_100': {'class': sklearn.neural_network.MLPClassifier, 'opts': {'hidden_layer_sizes': (100, 100, 100,)}},
    }

    classifiers_dict = {}
    for clf_name, clf_params in classifiers_params.items():
        clf1 = clf_params['class'](**clf_params['opts'])
        clf1.fit(X_train, y_train)
        classifiers_dict[clf_name] = clf1

    y_pred_train = {}
    for clf_name, clf_obj in classifiers_dict.items():
        y_pred_train[clf_name] = clf_obj.predict(X_train)

    metrics_train = {}
    for clf_name, clf_obj in classifiers_dict.items():
        precision, recall, f1score, _ = sklearn.metrics.precision_recall_fscore_support(y_train, y_pred_train[clf_name])
        metrics_train[clf_name] = {'precision': precision, 'recall': recall, 'f1': f1score}

    fig1 = matplotlib.pyplot.figure(figsize=(8, 5))
    ax1 = fig1.add_subplot(1, 1, 1)
    pandas.DataFrame({clf_name: clf_dict['precision'] for clf_name, clf_dict in metrics_train.items()}).plot.bar(ax=ax1)
    fig1.canvas.draw()
    test_framework.handle_figure_retention(fig1, "01_classifier_precision_train_bar.png")

    for clf_name, clf_obj in classifiers_dict.items():
        with open(f'{clf_name}.pkl', 'wb') as f:
            pickle.dump(clf_obj, f, protocol=5)

    stats_dict = {
        'input_mean': [float(v1) for v1 in input_scaler.mean_],
        'input_scale': [float(v1) for v1 in input_scaler.scale_],
        'target_classes': list(target_encoder.classes_),
    }
    with open('stats.json', 'w') as stats_file:
        json.dump(stats_dict, stats_file)

    km_clusterer = sklearn.cluster.KMeans(n_clusters=5)
    km_clusterer.fit(X_train)

    subset_df = zones_df[(zones_df['scenario'] == 'ssp434') & (zones_df['period_start'] == 2071)]
    zones_clustered = subset_df[['lat', 'lon', 'climate_group']].reset_index().drop('index', axis='columns')
    zones_clustered['climate_group_learned'] = km_clusterer.predict(input_scaler.transform(subset_df[predictors]))

    fig2 = matplotlib.pyplot.figure(figsize=(6, 5))
    ax2 = fig2.add_subplot(1, 1, 1)
    zones_clustered['climate_group_learned'].value_counts().plot.bar(ax=ax2)
    fig2.canvas.draw()
    test_framework.handle_figure_retention(fig2, "02_kmeans_cluster_label_distribution_bar.png")

if __name__ == "__main__":
    sys.exit(test_framework.execute_workflow(run_notebook_derived_workflow))
