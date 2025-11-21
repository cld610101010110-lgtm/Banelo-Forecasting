# ML Models Directory

This directory stores trained machine learning models for forecasting.

## Files

Place your trained model here:
- `forecasting_model.pkl` - The trained ML model from Google Colab

## Usage

1. Train model in Google Colab using `forecasting_model_training.ipynb`
2. Download `forecasting_model.pkl` from Colab
3. Place it in this directory
4. Run `python integrate_ml_model.py` to integrate with Django

## Security Note

**IMPORTANT:** Model files (.pkl) should NOT be committed to Git as they:
- Can be very large (>100MB)
- May contain sensitive training data
- Should be versioned separately

Model files are automatically excluded via `.gitignore`.

## Model Versioning

For production use, consider:
- Storing models in cloud storage (S3, Google Cloud Storage)
- Versioning models with timestamps (e.g., `model_2025-01-15.pkl`)
- Keeping metadata about each model version
- Automating model deployment via CI/CD

## Expected Model Format

The model file should be a pickle containing:
```python
{
    'model': <trained_model_object>,
    'metadata': {
        'model_name': str,
        'model_type': str,
        'trained_date': str,
        'metrics': dict,
        ...
    },
    'label_encoder': <LabelEncoder_object>,
    'feature_columns': list
}
```
