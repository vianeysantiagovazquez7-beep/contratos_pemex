cat > build.sh << 'EOF'
#!/usr/bin/env bash
set -o errexit

# Instalar Tesseract OCR
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-spa

pip install -r requirements.txt
EOF

# 3. Hacer ejecutable el build.sh
chmod +x build.sh