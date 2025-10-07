module.exports = {
  apps: [
    {
      name: "Hidecv-api_2025",
      cwd: "/home/ducchinh/Code/NEW_CHE_CV",   // <== thêm dòng này
      script: "venv/bin/python",
      args: "-m gunicorn -w 3 -k gthread --threads 3 --timeout 300 --bind 0.0.0.0:8000 main_gunicorn:app",
      env: {
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};
