# Render Backend Deployment Troubleshooting

## Current Error Analysis

The error shows:
```
==> Running build command 'cd backend && pip install -r requirements.txt'...
bash: line 1: cd: backend: No such file or directory
```

This means Render is NOT using the render.yaml configuration file.

## Possible Causes & Solutions

### 1. Manual Configuration Override
**Problem**: Render dashboard has manual build/start commands that override render.yaml
**Solution**: 
1. Go to Render dashboard → Your service → Settings
2. Check "Build Command" and "Start Command" fields
3. If they contain manual commands, clear them to use render.yaml
4. Redeploy

### 2. Wrong Repository Root
**Problem**: Render is looking in wrong directory
**Solution**:
1. Verify render.yaml is at repository root (not inside StorySign_Platform/)
2. Ensure repository structure is correct

### 3. Render Not Finding render.yaml
**Problem**: Configuration file not detected
**Solution**:
1. Ensure render.yaml is committed and pushed to GitHub
2. Check file is at repository root
3. Verify YAML syntax is valid

### 4. Service Configuration Issue
**Problem**: Service was created with manual settings
**Solution**:
1. Delete current service in Render
2. Create new service using "Blueprint" option
3. Point to repository with render.yaml

## Correct Configuration

The render.yaml should contain:
```yaml
services:
  - type: web
    buildCommand: "cd StorySign_Platform/backend && pip install -r requirements_minimal.txt"
    startCommand: "cd StorySign_Platform/backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api_simple:app --bind 0.0.0.0:$PORT"
```

## Verification Steps

1. Check render.yaml exists at repository root
2. Verify paths point to StorySign_Platform/backend
3. Confirm files exist: main_api_simple.py, requirements_minimal.txt
4. Ensure no duplicate render.yaml files
5. Check Render dashboard for manual overrides

## If Still Failing

Try creating the service as a "Blueprint" in Render:
1. Go to Render dashboard
2. Click "New +" → "Blueprint"
3. Connect to your GitHub repository
4. Render will automatically use render.yaml
