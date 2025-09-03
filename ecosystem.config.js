module.exports = {
  apps: [{
    name: 'steep-backend',
    cwd: './backend',
    script: 'venv/bin/uvicorn',
    args: 'server:app --host 0.0.0.0 --port 8001',
    env: {
      NODE_ENV: 'production'
    }
  }, {
    name: 'steep-frontend',
    cwd: './frontend',
    script: 'npx',
    args: 'serve -s build -l 3000',
    env: {
      NODE_ENV: 'production'
    }
  }]
}