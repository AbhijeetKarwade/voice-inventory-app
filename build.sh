services:
  - type: web
    name: voice-inventory-manager
    env: python
    plan: free
    buildCommand: ./build.sh
    startCommand: gunicorn app:app
    disk:
      name: data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
    envVars:
      - key: PYTHON_VERSION
        value: 3.9
      - key: HOST
        value: 0.0.0.0
      - key: PORT
        value: 8000
      - key: DATA_DIR
        value: /opt/render/project/src/data
      - key: RENDER
        value: true