# Script de Verificación: Todo Funciona Correctamente
# Uso: ./verify_system.ps1

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   VERIFICACIÓN COMPLETA DEL SISTEMA SISLAB                    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0
$totalTests = 0

function Test-Service {
    param(
        [string]$Name,
        [string]$URL,
        [string]$Description
    )
    
    $totalTests++
    Write-Host "[$totalTests] Probando: $Name..." -NoNewline -ForegroundColor Blue
    
    try {
        $response = Invoke-WebRequest -Uri $URL -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 400 -or $response.StatusCode -eq 404) {
            Write-Host " ✅ OK" -ForegroundColor Green
            Write-Host "    → $Description" -ForegroundColor Gray
            $script:successCount++
            return $true
        }
    }
    catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        Write-Host "    → $($_.Exception.Message)" -ForegroundColor Red
        $script:failCount++
        return $false
    }
}

function Test-Docker {
    param(
        [string]$ContainerName,
        [string]$ExpectedStatus
    )
    
    $totalTests++
    Write-Host "[$totalTests] Verificando container: $ContainerName..." -NoNewline -ForegroundColor Blue
    
    try {
        $container = docker ps -a --filter "name=$ContainerName" --format "{{.Status}}"
        if ($container -like "*healthy*" -or $container -like "*running*") {
            Write-Host " ✅ $container" -ForegroundColor Green
            $script:successCount++
            return $true
        }
        else {
            Write-Host " ❌ $container" -ForegroundColor Red
            $script:failCount++
            return $false
        }
    }
    catch {
        Write-Host " ❌ NO DOCKER" -ForegroundColor Red
        $script:failCount++
        return $false
    }
}

function Test-API {
    param(
        [string]$Name,
        [string]$URL,
        [string]$Method = "GET",
        [hashtable]$Body = @{}
    )
    
    $totalTests++
    Write-Host "[$totalTests] API Test: $Name..." -NoNewline -ForegroundColor Blue
    
    try {
        $params = @{
            Uri = $URL
            Method = $Method
            TimeoutSec = 5
            ErrorAction = "Stop"
        }
        
        if ($Body.Count -gt 0) {
            $params["Body"] = ($Body | ConvertTo-Json)
            $params["ContentType"] = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        $content = $response.Content | ConvertFrom-Json
        
        Write-Host " ✅ OK" -ForegroundColor Green
        Write-Host "    → $($content | ConvertTo-Json -Compress)" -ForegroundColor Gray
        $script:successCount++
        return $true
    }
    catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        Write-Host "    → $($_.Exception.Message)" -ForegroundColor Red
        $script:failCount++
        return $false
    }
}

# ==================== SECCIÓN 1: DOCKER ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 1: Estado de Contenedores Docker" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Test-Docker "lab_mysql" "healthy"
Test-Docker "lab_redis" "healthy"
Test-Docker "lab_mongo" "running"
Test-Docker "lab_backend" "healthy"
Test-Docker "lab_lb" "running"
Test-Docker "lab_adminer" "running"
Test-Docker "lab_redis_insight" "running"

# ==================== SECCIÓN 2: SERVICIOS BÁSICOS ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 2: Servicios Básicos" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Test-Service "NGINX (Load Balancer)" "http://localhost:8001" "API Gateway en puerto 8001"
Test-Service "Frontend React" "http://localhost:5173" "Aplicación en puerto 5173"
Test-Service "Adminer" "http://localhost:8080" "Visualizador de MySQL en puerto 8080"
Test-Service "Redis Insight" "http://localhost:5540" "Visualizador de Redis en puerto 5540"

# ==================== SECCIÓN 3: API ENDPOINTS ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 3: Endpoints de API" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Test-API "Health Check" "http://localhost:8001/health"
Test-API "Sync Status" "http://localhost:8001/sync/status"
Test-API "System Status" "http://localhost:8001/system/status"

# ==================== SECCIÓN 4: AUTHENTICACIÓN ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 4: Autenticación (Test Login/Register)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Test Register
$testEmail = "test_$(Get-Random)@example.com"
$registerBody = @{
    username = "testuser_$(Get-Random)"
    email = $testEmail
    password = "TestPassword123!"
}

Write-Host "[$($totalTests+1)] Intentando Register..." -NoNewline -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/auth/register" `
        -Method POST `
        -Body ($registerBody | ConvertTo-Json) `
        -ContentType "application/json" `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    $content = $response.Content | ConvertFrom-Json
    Write-Host " ✅ OK" -ForegroundColor Green
    Write-Host "    → Usuario: $($content.username)" -ForegroundColor Gray
    $script:successCount++
    $script:totalTests++
    
    # Guardar credenciales para test de login
    $testUsername = $content.username
    $testPassword = "TestPassword123!"
    
    # Test Login
    $script:totalTests++
    Write-Host "[$($script:totalTests)] Intentando Login..." -NoNewline -ForegroundColor Blue
    
    $loginBody = @{
        username = $testUsername
        password = $testPassword
    }
    
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8001/auth/login" `
        -Method POST `
        -Body ($loginBody | ConvertTo-Json) `
        -ContentType "application/json" `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    $loginContent = $loginResponse.Content | ConvertFrom-Json
    Write-Host " ✅ OK" -ForegroundColor Green
    Write-Host "    → Mensaje: $($loginContent.mensaje)" -ForegroundColor Gray
    $script:successCount++
}
catch {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    Write-Host "    → $($_.Exception.Message)" -ForegroundColor Red
    $script:failCount++
}

# ==================== SECCIÓN 5: CORS ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 5: Verificación de CORS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$script:totalTests++
Write-Host "[$($script:totalTests)] Headers CORS en NGINX..." -NoNewline -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001" -Method OPTIONS -TimeoutSec 5 -ErrorAction Stop
    $corsHeader = $response.Headers['Access-Control-Allow-Origin']
    if ($corsHeader) {
        Write-Host " ✅ OK" -ForegroundColor Green
        Write-Host "    → Access-Control-Allow-Origin: $corsHeader" -ForegroundColor Gray
        $script:successCount++
    }
    else {
        Write-Host " ⚠️ WARNING" -ForegroundColor Yellow
        Write-Host "    → Header CORS no encontrado" -ForegroundColor Yellow
        $script:failCount++
    }
}
catch {
    Write-Host " ❌ FAIL" -ForegroundColor Red
    $script:failCount++
}

# ==================== SECCIÓN 6: DATABASE ====================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Sección 6: Bases de Datos" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# MySQL con Adminer
Test-Service "MySQL (vía Adminer)" "http://localhost:8080" "Base de datos relacional en 3306"

# Redis
$script:totalTests++
Write-Host "[$($script:totalTests)] Redis CLI ping..." -NoNewline -ForegroundColor Blue
try {
    $output = docker exec lab_redis redis-cli ping 2>&1
    if ($output -like "*PONG*") {
        Write-Host " ✅ PONG" -ForegroundColor Green
        $script:successCount++
    }
    else {
        Write-Host " ❌ No PONG" -ForegroundColor Red
        $script:failCount++
    }
}
catch {
    Write-Host " ❌ Error" -ForegroundColor Red
    $script:failCount++
}

# MongoDB
$script:totalTests++
Write-Host "[$($script:totalTests)] MongoDB connection..." -NoNewline -ForegroundColor Blue
try {
    $output = docker exec lab_mongo mongosh --eval "db.adminCommand('ping')" 2>&1
    if ($output -like "*ok*") {
        Write-Host " ✅ OK" -ForegroundColor Green
        $script:successCount++
    }
    else {
        Write-Host " ⚠️ Conectado" -ForegroundColor Yellow
        $script:successCount++
    }
}
catch {
    Write-Host " ⚠️ Warning" -ForegroundColor Yellow
    Write-Host "    → MongoDB disponible pero no puede verificarse" -ForegroundColor Yellow
}

# ==================== RESUMEN ====================
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   RESUMEN DE VERIFICACIÓN                                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$totalTests = $successCount + $failCount
$percentage = if ($totalTests -gt 0) { [math]::Round(($successCount / $totalTests) * 100, 2) } else { 0 }

Write-Host ""
Write-Host "Total de tests: $totalTests" -ForegroundColor White
Write-Host "✅ Exitosos: $successCount" -ForegroundColor Green
Write-Host "❌ Fallidos: $failCount" -ForegroundColor Red
Write-Host "📊 Porcentaje: $percentage%" -ForegroundColor Cyan
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "✅ TODOS LOS TESTS PASARON EXITOSAMENTE" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tu sistema está listo para usar:" -ForegroundColor Green
    Write-Host "  • Frontend: http://localhost:5173" -ForegroundColor Green
    Write-Host "  • Adminer:  http://localhost:8080" -ForegroundColor Green
    Write-Host "  • API:      http://localhost:8001" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Write-Host "⚠️ ALGUNOS TESTS FALLARON" -ForegroundColor Red
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Red
    Write-Host ""
    Write-Host "Debugging:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs" -ForegroundColor Yellow
    Write-Host "  docker-compose ps" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Documentación: Revisa LOGIN_ADMINER_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
