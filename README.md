# Ink/Stitch Conversion Service

This Docker service provides professional SVG to DST conversion using Ink/Stitch for embroidery applications.

## Features

- **Professional Conversion**: Uses Ink/Stitch for industry-standard DST files
- **Garment-Specific Settings**: Optimized for hat, shirt, and jacket embroidery
- **Optimal Sizing**: Automatic scaling based on embroidery best practices
- **REST API**: Simple HTTP interface for integration

## Quick Start

1. **Build and run with Docker Compose:**
   ```bash
   cd docker
   docker-compose up --build
   ```

2. **Test the service:**
   ```bash
   curl http://localhost:5000/health
   ```

## API Endpoints

### Health Check
```
GET /health
```
Returns service status.

### File Conversion
```
POST /convert
Content-Type: multipart/form-data

Fields:
- svg_file: SVG file to convert
- garment_type: hat, shirt, or jacket
```
Returns DST file download.

### JSON Conversion (for edge functions)
```
POST /test-conversion
Content-Type: application/json

{
  "svg_content": "<svg>...</svg>",
  "garment_type": "hat",
  "filename": "design.svg"
}
```
Returns JSON with base64-encoded DST content.

## Garment Settings

### Hat (Front Panel)
- Max size: 1.75" × 1.75" (44.45mm)
- High density: 4.0 lines/mm
- Underlay: Yes
- Pull compensation: 0.2mm

### Shirt (Left Chest)
- Max size: 2.5" × 3.5" (63.5mm × 88.9mm)
- Medium density: 3.5 lines/mm
- Underlay: Yes
- Pull compensation: 0.15mm

### Jacket (Back Center)
- Max size: 5" × 6" (127mm × 152.4mm)
- Lower density: 3.0 lines/mm
- Underlay: No (less dense for larger areas)
- Pull compensation: 0.1mm

## Deployment Options

### Option 1: Local Development
```bash
docker-compose up --build
```

### Option 2: Cloud Deployment
Deploy to any cloud provider that supports Docker containers:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- DigitalOcean Apps

### Option 3: VPS Deployment
```bash
# Copy files to server
scp -r docker/ user@your-server:/opt/inkstitch-converter/

# SSH to server and run
ssh user@your-server
cd /opt/inkstitch-converter
docker-compose up -d
```

## Environment Variables

Set these in your edge function environment:

```bash
CONVERTER_SERVICE_URL=http://your-converter-service:5000
```

## Integration with Supabase

Update your `convert-svg-to-dst` edge function to use this service:

1. Deploy the conversion service
2. Set `CONVERTER_SERVICE_URL` environment variable
3. The edge function will call this service for conversions

## Troubleshooting

### Service won't start
- Check Docker is running
- Ensure port 5000 is available
- Check logs: `docker-compose logs inkstitch-converter`

### Conversion fails
- Verify SVG is valid
- Check SVG contains drawable paths/shapes
- Ensure garment_type is valid (hat/shirt/jacket)

### Memory issues
- Increase Docker memory limit in docker-compose.yml
- Monitor conversion logs for memory errors

## Production Considerations

1. **Scaling**: Use container orchestration for multiple instances
2. **Security**: Run behind reverse proxy with rate limiting
3. **Monitoring**: Add health checks and logging
4. **Persistence**: Consider volume mounts for temporary files
5. **Network**: Use private networking between edge functions and service 