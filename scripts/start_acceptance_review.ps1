$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$checklistPath = Join-Path $projectRoot "REVISION_VISUAL_PUBLICACION.md"
$publicAppPath = Join-Path $projectRoot "streamlit_app.py"
$updaterPath = Join-Path $projectRoot "fq_observatorio\updater.py"

function Resolve-FranQuestionsPython {
    $candidates = @()
    $localPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $localPython) {
        $candidates += ,@($localPython)
    }

    $workspacePython = Join-Path (Split-Path -Parent $projectRoot) "outputs\FranQuestions\Version actual\FranQuestions_Observatorio_v1.1.0\.venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $workspacePython) {
        $candidates += ,@($workspacePython)
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidates += ,@("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidates += ,@("python")
    }

    foreach ($candidate in $candidates) {
        $executable = $candidate[0]
        $prefix = @($candidate | Select-Object -Skip 1)
        try {
            & $executable @prefix -c "import streamlit, reportlab" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
            continue
        }
    }

    throw "No se encontro una instalacion de Python con Streamlit y ReportLab. Ejecute primero INSTALAR_FRANQUESTIONS.cmd o revise la instalacion actual."
}

function Test-PortInUse([int]$Port) {
    return $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Start-FranQuestionsApp {
    param(
        [string]$Label,
        [string]$AppPath,
        [int]$Port,
        [array]$PythonCommand
    )

    if (Test-PortInUse -Port $Port) {
        Write-Host "$Label ya estaba abierto en el puerto $Port."
        return
    }

    $executable = $PythonCommand[0]
    $arguments = @($PythonCommand | Select-Object -Skip 1)
    $arguments += @(
        "-m", "streamlit", "run", $AppPath,
        "--server.port", "$Port",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    )

    Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Minimized | Out-Null
    Write-Host "$Label iniciado en http://127.0.0.1:$Port"
}

foreach ($requiredPath in @($checklistPath, $publicAppPath, $updaterPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Falta un archivo necesario: $requiredPath"
    }
}

$pythonCommand = Resolve-FranQuestionsPython
Start-FranQuestionsApp -Label "Observatorio" -AppPath $publicAppPath -Port 8501 -PythonCommand $pythonCommand
Start-FranQuestionsApp -Label "Actualizador privado" -AppPath $updaterPath -Port 8503 -PythonCommand $pythonCommand

Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8501" | Out-Null
Start-Process "http://127.0.0.1:8503" | Out-Null
Start-Process notepad.exe -ArgumentList $checklistPath | Out-Null

Write-Host "Revision preparada. Se abrieron el Observatorio, el actualizador y la lista de comprobacion."
