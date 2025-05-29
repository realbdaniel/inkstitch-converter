#!/usr/bin/env python3
"""
Flask API server for SVG to DST conversion using Ink/Stitch
"""

import os
import tempfile
import uuid
from flask import Flask, request, jsonify, send_file
import subprocess
import json
from pathlib import Path

app = Flask(__name__)

# Configure upload limits
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'inkstitch-converter'})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Ink/Stitch Converter',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'convert': '/convert (POST)',
            'test-conversion': '/test-conversion (POST)'
        }
    })

@app.route('/convert', methods=['POST'])
def convert_svg_to_dst():
    """
    Convert SVG to DST endpoint
    Expects: multipart/form-data with 'svg_file' and 'garment_type'
    Returns: DST file or error
    """
    try:
        # Validate request
        if 'svg_file' not in request.files:
            return jsonify({'error': 'No SVG file provided'}), 400
        
        svg_file = request.files['svg_file']
        garment_type = request.form.get('garment_type', 'hat')
        
        if svg_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if garment_type not in ['hat', 'shirt', 'jacket']:
            return jsonify({'error': 'Invalid garment type'}), 400
        
        # Validate SVG file
        if not svg_file.filename.lower().endswith('.svg'):
            return jsonify({'error': 'File must be an SVG'}), 400
        
        # Create temporary directory for this conversion
        temp_dir = tempfile.mkdtemp()
        conversion_id = str(uuid.uuid4())
        
        try:
            # Save uploaded SVG
            svg_path = os.path.join(temp_dir, f'{conversion_id}.svg')
            svg_file.save(svg_path)
            
            # Output DST path
            dst_path = os.path.join(temp_dir, f'{conversion_id}.dst')
            
            # Call conversion script
            cmd = ['python3', '/opt/convert.py', svg_path, dst_path, garment_type]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse conversion result
                try:
                    conversion_result = json.loads(result.stdout)
                    
                    if os.path.exists(dst_path):
                        # Return the DST file
                        return send_file(
                            dst_path,
                            as_attachment=True,
                            download_name=f'{svg_file.filename.rsplit(".", 1)[0]}.dst',
                            mimetype='application/octet-stream'
                        )
                    else:
                        return jsonify({'error': 'DST file was not generated'}), 500
                        
                except json.JSONDecodeError:
                    return jsonify({'error': 'Invalid conversion result'}), 500
            else:
                # Parse error from conversion script
                try:
                    error_result = json.loads(result.stderr)
                    return jsonify({'error': error_result.get('error', 'Conversion failed')}), 500
                except json.JSONDecodeError:
                    return jsonify({'error': f'Conversion failed: {result.stderr}'}), 500
                
        finally:
            # Clean up temporary files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/test-conversion', methods=['POST'])
def test_conversion():
    """
    Test conversion endpoint with JSON payload
    For testing from edge functions
    """
    try:
        data = request.get_json()
        
        if not data or 'svg_content' not in data:
            return jsonify({'error': 'No SVG content provided'}), 400
        
        svg_content = data['svg_content']
        garment_type = data.get('garment_type', 'hat')
        filename = data.get('filename', 'design.svg')
        
        if garment_type not in ['hat', 'shirt', 'jacket']:
            return jsonify({'error': 'Invalid garment type'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        conversion_id = str(uuid.uuid4())
        
        try:
            # Save SVG content
            svg_path = os.path.join(temp_dir, f'{conversion_id}.svg')
            with open(svg_path, 'w') as f:
                f.write(svg_content)
            
            # Output DST path
            dst_path = os.path.join(temp_dir, f'{conversion_id}.dst')
            
            # Call conversion script
            cmd = ['python3', '/opt/convert.py', svg_path, dst_path, garment_type]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Read DST file and return as base64
                if os.path.exists(dst_path):
                    import base64
                    with open(dst_path, 'rb') as f:
                        dst_content = f.read()
                    
                    dst_base64 = base64.b64encode(dst_content).decode('utf-8')
                    
                    return jsonify({
                        'success': True,
                        'dst_content': dst_base64,
                        'garment_type': garment_type,
                        'file_size': len(dst_content),
                        'filename': filename.replace('.svg', '.dst')
                    })
                else:
                    return jsonify({'error': 'DST file was not generated'}), 500
            else:
                return jsonify({'error': f'Conversion failed: {result.stderr}'}), 500
                
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Initialize virtual display when running directly
def init_display():
    """Initialize virtual display for headless operation"""
    try:
        # Start virtual display for headless operation
        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Warning: Could not start virtual display: {e}")

if __name__ == '__main__':
    init_display()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # When running with gunicorn, initialize display once
    init_display() 