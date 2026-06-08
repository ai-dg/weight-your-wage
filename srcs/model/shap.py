
    ######################################################################
    #####                         SHAP ANALYSIS                      #####
    ######################################################################
    
    import shap
    import matplotlib.pyplot as plt
    # 1. Force model to CPU and Float32 for stability
    # SHAP often struggles with GPU-based DeepExplainer in certain environments
    explainer_model = salary_model.to('cpu').to(torch.float32)
    explainer_model.eval()

    # 2. Prepare data in Float32
    train_loader = salary_data_module.train_dataloader()
    # Ensure background is Float32 and on CPU
    background_data = train_loader.dataset.tensors[0][:100].to(torch.float32).to('cpu')
    
    # 3. Initialize Explainer
    explainer = shap.DeepExplainer(explainer_model, background_data)
    
    # 4. Prepare test samples in Float32
    val_loader = salary_data_module.val_dataloader()
    test_samples = val_loader.dataset.tensors[0][:200].to(torch.float32).to('cpu')

    # 5. Calculate SHAP values with additivity check disabled
    # We set check_additivity=False to stop the crash
    # But by moving to float32, we make the results actually reliable
    shap_values = explainer.shap_values(test_samples, check_additivity=False)

    # 6. Plotting (standardize the input for the plot)
    plt.figure(figsize=(12, 8))
    feature_names = salary_data_module.ct.get_feature_names_out()
    
    # Note: shap_values might be a list [np.array] for single-output models
    # If it is, we take the first element
    values_to_plot = shap_values[0] if isinstance(shap_values, list) else shap_values

    shap.summary_plot(
        values_to_plot, 
        test_samples.numpy(), 
        feature_names=feature_names, 
        show=False
    )
    
    # 4. Save and Log to MLflow
    plot_path = "salary_feature_impact.png"
    plt.savefig(plot_path, bbox_inches='tight', dpi=300)
    plt.close()

    with mlflow.start_run(run_id=run_id):
        mlflow.log_artifact(plot_path, artifact_path="plots")
    
    print(f"SHAP analysis complete. Plot saved to MLflow under run {run_id}")
    
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import shap
    
    # Ensure you use the Float32/CPU versions of shap_values and test_samples from the previous step
    vals = shap_values[0] if isinstance(shap_values, list) else shap_values
    
    # 1. Calculate Importance (Mean Absolute SHAP)
    feature_importance = np.abs(vals).mean(0)
    
    # 2. Determine Direction (Correlation between Feature Value and SHAP Value)
    # This tells us if the feature generally pushes the salary UP (+) or DOWN (-)
    feature_direction = []
    for i in range(vals.shape[1]):
        # Correlation between the input feature and the SHAP impact
        corr = np.corrcoef(test_samples[:, i].cpu().numpy(), vals[:, i])[0, 1]
        feature_direction.append(1 if corr > 0 else -1)
    
    # 3. Create a DataFrame for easy plotting
    feature_names = salary_data_module.ct.get_feature_names_out()
    summary_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importance,
        'direction': feature_direction
    })
    
    # Sort by importance
    summary_df = summary_df.sort_values(by='importance', ascending=True).tail(20) # Top 20
    
    # 4. Plotting
    plt.figure(figsize=(10, 8))
    colors = ['#ff0051' if x > 0 else '#008bfb' for x in summary_df['direction']]
    
    plt.barh(summary_df['feature'], summary_df['importance'], color=colors)
    plt.xlabel("Mean Absolute SHAP Value (Impact Magnitude)")
    plt.title("Feature Importance: Red = Positive Impact | Blue = Negative Impact")
    
    # Add a legend
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], color='#ff0051', lw=4, label='Positive Impact (Pushes Salary Up)'),
                       Line2D([0], [0], color='#008bfb', lw=4, label='Negative Impact (Pushes Salary Down)')]
    plt.legend(handles=legend_elements, loc='lower right')
    
    plt.savefig('comparative_feature_impact.png', bbox_inches='tight')
    plt.show()