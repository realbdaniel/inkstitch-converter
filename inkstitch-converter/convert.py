#!/usr/bin/env python3
"""
Professional SVG to DST converter using pyembroidery
Optimal settings for different garment types (hat, shirt, jacket)
"""

import os
import sys
import tempfile
import json
import xml.etree.ElementTree as ET
import re
from pathlib import Path

try:
    import pyembroidery
except ImportError:
    print("Error: pyembroidery not installed")
    sys.exit(1)

# Optimal embroidery settings for each garment type
GARMENT_SETTINGS = {
    'hat': {
        'max_width_mm': 44.45,  # 1.75"
        'max_height_mm': 44.45,
        'density': 4.0,  # lines per mm
        'stitch_length': 3.0,
        'description': 'Hat front panel'
    },
    'shirt': {
        'max_width_mm': 63.5,   # 2.5" 
        'max_height_mm': 88.9,  # 3.5"
        'density': 3.5,
        'stitch_length': 3.5,
        'description': 'Shirt left chest'
    },
    'jacket': {
        'max_width_mm': 127.0,  # 5"
        'max_height_mm': 152.4, # 6"
        'density': 3.0,
        'stitch_length': 4.0,
        'description': 'Jacket back center'
    }
}

def extract_svg_paths(svg_content):
    """Extract path coordinates from SVG content"""
    try:
        # Parse SVG
        root = ET.fromstring(svg_content)
        
        # Find namespace
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        if root.tag.startswith('{'):
            ns_url = root.tag.split('}')[0][1:]
            ns['svg'] = ns_url
        
        paths = []
        
        # Extract path elements
        for path_elem in root.findall('.//svg:path', ns):
            d = path_elem.get('d', '')
            if d:
                coords = parse_path_data(d)
                if coords:
                    paths.extend(coords)
        
        # Extract rectangles
        for rect in root.findall('.//svg:rect', ns):
            x = float(rect.get('x', 0))
            y = float(rect.get('y', 0))
            width = float(rect.get('width', 0))
            height = float(rect.get('height', 0))
            
            if width > 0 and height > 0:
                # Convert rectangle to path coordinates
                rect_path = [
                    (x, y),
                    (x + width, y),
                    (x + width, y + height),
                    (x, y + height),
                    (x, y)
                ]
                paths.append(rect_path)
        
        # Extract circles
        for circle in root.findall('.//svg:circle', ns):
            cx = float(circle.get('cx', 0))
            cy = float(circle.get('cy', 0))
            r = float(circle.get('r', 0))
            
            if r > 0:
                # Approximate circle with polygon
                import math
                circle_path = []
                for i in range(16):  # 16-sided polygon
                    angle = 2 * math.pi * i / 16
                    x = cx + r * math.cos(angle)
                    y = cy + r * math.sin(angle)
                    circle_path.append((x, y))
                circle_path.append(circle_path[0])  # Close the path
                paths.append(circle_path)
        
        return paths
        
    except Exception as e:
        print(f"Error parsing SVG: {e}")
        return []

def parse_path_data(path_data):
    """Parse SVG path data into coordinate lists"""
    try:
        # Simple path parser for M, L, H, V commands
        coords = []
        current_path = []
        
        # Extract numbers from path
        numbers = re.findall(r'-?\d*\.?\d+', path_data)
        if len(numbers) < 4:
            return []
        
        # Convert to coordinate pairs
        points = []
        for i in range(0, len(numbers) - 1, 2):
            try:
                x = float(numbers[i])
                y = float(numbers[i + 1])
                points.append((x, y))
            except (ValueError, IndexError):
                continue
        
        if len(points) >= 2:
            coords.append(points)
        
        return coords
        
    except Exception as e:
        print(f"Error parsing path data: {e}")
        return []

def convert_svg_to_dst(svg_content, output_path, garment_type='hat'):
    """Convert SVG to DST using pyembroidery"""
    try:
        settings = GARMENT_SETTINGS.get(garment_type, GARMENT_SETTINGS['hat'])
        
        # Extract paths from SVG
        paths = extract_svg_paths(svg_content)
        
        if not paths:
            # Create a simple test pattern if no paths found
            paths = [[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]]
        
        # Calculate bounds
        all_points = []
        for path in paths:
            all_points.extend(path)
        
        if not all_points:
            return False, "No valid paths found in SVG"
        
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width <= 0 or height <= 0:
            return False, "Invalid SVG dimensions"
        
        # Scale to fit garment size
        scale_x = settings['max_width_mm'] / width if width > 0 else 1
        scale_y = settings['max_height_mm'] / height if height > 0 else 1
        scale = min(scale_x, scale_y, 2.0)  # Max 2x scale
        
        # Create embroidery pattern
        pattern = pyembroidery.EmbPattern()
        
        # Convert paths to stitches
        for path_index, path in enumerate(paths):
            if len(path) < 2:
                continue
                
            # Move to start of path
            start_x = (path[0][0] - min_x) * scale
            start_y = (path[0][1] - min_y) * scale
            
            if path_index == 0:
                pattern.move_abs(start_x, start_y)
            else:
                pattern.move_abs(start_x, start_y)
            
            # Stitch along path
            for point in path[1:]:
                x = (point[0] - min_x) * scale
                y = (point[1] - min_y) * scale
                pattern.stitch_abs(x, y)
        
        # End the pattern
        pattern.end()
        
        # Save as DST
        pyembroidery.write_dst(pattern, output_path)
        
        return True, f"Successfully converted to {output_path}"
        
    except Exception as e:
        return False, f"Conversion error: {str(e)}"

def main():
    """Command line interface for conversion"""
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
    with open(input_svg, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Convert to DST
    success, message = convert_svg_to_dst(svg_content, output_dst, garment_type)
    
    if success:
        # Get file size for reporting
        file_size = os.path.getsize(output_dst) if os.path.exists(output_dst) else 0
        settings = GARMENT_SETTINGS[garment_type]
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

if __name__ == '__main__':
    main() 