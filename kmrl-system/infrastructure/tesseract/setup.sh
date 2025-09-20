#!/bin/bash
# Tesseract OCR Setup for KMRL Knowledge Hub

# Install Tesseract OCR
sudo apt-get update
sudo apt-get install -y tesseract-ocr

# Install Malayalam language pack
sudo apt-get install -y tesseract-ocr-mal

# Install additional language packs
sudo apt-get install -y tesseract-ocr-eng

# Verify installation
tesseract --version
tesseract --list-langs

# Create test script
cat > test_ocr.sh << 'EOF'
#!/bin/bash
# Test OCR with Malayalam and English
echo "Testing Malayalam OCR..."
echo "ഹലോ ലോകം" | tesseract stdin stdout -l mal+eng

echo "Testing English OCR..."
echo "Hello World" | tesseract stdin stdout -l eng
EOF

chmod +x test_ocr.sh

echo "Tesseract OCR setup complete!"
echo "Available languages:"
tesseract --list-langs
