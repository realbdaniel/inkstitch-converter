#!/usr/bin/env python3
"""
Professional SVG to DST converter using Ink/Stitch
Optimal settings for different garment types (hat, shirt, jacket)
"""

import os
import sys
import tempfile
import json
import subprocess
from pathlib import Path

# Optimal embroidery settings for each garment type
GARMENT_SETTINGS = {
    'hat': {
        'max_width_mm': 44.45,  # 1.75"
        'max_height_mm': 44.45,
        'density': 4.0,  # lines per mm
        'underlay': True,
        'pull_compensation': 0.2,
        'max_stitch_length': 3.0
    },
    'shirt': {
        'max_width_mm': 63.5,   # 2.5" 
        'max_height_mm': 88.9,  # 3.5"
        'density': 3.5,
        'underlay': True,
        'pull_compensation': 0.15,
        'max_stitch_length': 3.5
    },
    'jacket': {
        'max_width_mm': 127.0,  # 5"
        'max_height_mm': 152.4, # 6"
        'density': 3.0,
        'underlay': False,  # Less dense for larger areas
        'pull_compensation': 0.1,
        'max_stitch_length': 4.0
    }
}

def prepare_svg_for_embroidery(svg_content, garment_type='hat'):
    """
    Prepare SVG file with optimal settings for embroidery
    """
    settings = GARMENT_SETTINGS.get(garment_type, GARMENT_SETTINGS['hat'])
    
    # Create temporary SVG file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_svg:
        # Add Ink/Stitch specific attributes to SVG
        enhanced_svg = add_inkstitch_attributes(svg_content, settings)
        temp_svg.write(enhanced_svg)
        temp_svg_path = temp_svg.name
    
    return temp_svg_path, settings

def add_inkstitch_attributes(svg_content, settings):
    """
    Add Ink/Stitch specific attributes for optimal embroidery
    """
    # Basic approach: add inkstitch namespace and default fill settings
    
    # Add inkstitch namespace if not present
    if 'xmlns:inkstitch' not in svg_content:
        svg_content = svg_content.replace(
            '<svg',
            '<svg xmlns:inkstitch="http://inkstitch.org/namespace"'
        )
    
    # Add default fill parameters to paths
    import re
    
    def add_fill_params(match):
        path_tag = match.group(0)
        
        # Don't modify if already has inkstitch attributes
        if 'inkstitch:' in path_tag:
            return path_tag
        
        # Add fill density and other settings
        fill_attrs = [
            f'inkstitch:auto_fill="true"',
            f'inkstitch:angle="45"',
            f'inkstitch:row_spacing_mm="{1.0/settings["density"]:.2f}"',
            f'inkstitch:max_stitch_length_mm="{settings["max_stitch_length"]}"',
            f'inkstitch:staggers="4"'
        ]
        
        if settings['underlay']:
            fill_attrs.extend([
                f'inkstitch:underlay="true"',
                f'inkstitch:underlay_angle="15"',
                f'inkstitch:underlay_row_spacing_mm="{2.0/settings["density"]:.2f}"'
            ])
        
        # Insert before the closing >
        if path_tag.endswith('/>'):
            return path_tag[:-2] + ' ' + ' '.join(fill_attrs) + ' />'
        else:
            return path_tag[:-1] + ' ' + ' '.join(fill_attrs) + '>'
    
    # Apply to all path elements
    svg_content = re.sub(r'<path[^>]*>', add_fill_params, svg_content)
    
    return svg_content

def convert_svg_to_dst(svg_path, output_path, garment_type='hat'):
    """
    Convert SVG to DST using Ink/Stitch
    """
    try:
        # Use Ink/Stitch via Inkscape CLI
        cmd = [
            'inkscape',
            '--batch-process',
            '--verb=org.inkstitch.embroider_settings',
            '--verb=org.inkstitch.embroider',
            '--verb=FileSave',
            '--verb=FileQuit',
            svg_path
        ]
        
        # Set environment for headless operation
        env = os.environ.copy()
        env['DISPLAY'] = ':99'
        
        # Start virtual display
        subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Run conversion
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        
        if result.returncode == 0:
            # Look for generated DST file
            dst_file = svg_path.replace('.svg', '.dst')
            if os.path.exists(dst_file):
                # Move to desired output location
                os.rename(dst_file, output_path)
                return True, f"Successfully converted to {output_path}"
            else:
                return False, "DST file was not generated"
        else:
            return False, f"Inkscape error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Conversion timed out"
    except Exception as e:
        return False, f"Conversion error: {str(e)}"

def main():
    """
    Command line interface for conversion
    """
    if len(sys.argv) != 4:
        print("Usage: python convert.py <input.svg> <output.dst> <garment_type>")
        print("garment_type: hat, shirt, or jacket")
        sys.exit(1)
    
    input_svg = sys.argv[1]
    output_dst = sys.argv[2]
    garment_type = sys.argv[3]
    
    if garment_type not in GARMENT_SETTINGS:
        print(f"Invalid garment type: {garment_type}")
        print("Valid types: hat, shirt, jacket")
        sys.exit(1)
    
    if not os.path.exists(input_svg):
        print(f"Input file not found: {input_svg}")
        sys.exit(1)
    
    # Read SVG content
    with open(input_svg, 'r') as f:
        svg_content = f.read()
    
    # Prepare SVG with embroidery settings
    prepared_svg, settings = prepare_svg_for_embroidery(svg_content, garment_type)
    
    try:
        # Convert to DST
        success, message = convert_svg_to_dst(prepared_svg, output_dst, garment_type)
        
        if success:
            # Get file size for reporting
            file_size = os.path.getsize(output_dst)
            result = {
                'success': True,
                'output_file': output_dst,
                'garment_type': garment_type,
                'settings': settings,
                'file_size': file_size,
                'message': message
            }
            print(json.dumps(result))
        else:
            result = {
                'success': False,
                'error': message,
                'garment_type': garment_type
            }
            print(json.dumps(result), file=sys.stderr)
            sys.exit(1)
            
    finally:
        # Clean up temporary file
        if os.path.exists(prepared_svg):
            os.unlink(prepared_svg)

if __name__ == '__main__':
    main() 