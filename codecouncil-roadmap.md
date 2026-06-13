# CodeCouncil Roadmap

## Visión

**CodeCouncil** es un framework extensible de revisión multidisciplinaria de proyectos de software mediante agentes especializados, herramientas deterministas, validación crítica de hallazgos y consolidación en reportes accionables.

Su propósito no es producir más texto, sino mejorar la calidad de las decisiones técnicas.

CodeCouncil debe permitir que una persona, desde Claude Code u otro coding agent compatible, ejecute una única orden como:

```text
/project-review full
```

y obtenga una revisión consolidada desde distintas perspectivas:

- Arquitectura de software
- Calidad y mantenibilidad del código
- QA y estrategia de pruebas
- Seguridad de aplicaciones
- SRE y operabilidad
- UX y accesibilidad
- Diseño de APIs
- Privacidad y gobierno de datos
- FinOps
- Producto
- Seguridad y calidad de sistemas de IA

La experiencia para el usuario debe ser simple, aunque internamente exista una arquitectura de múltiples etapas y agentes.

---

# 1. Principios de diseño

## 1.1. Un único punto de entrada

El usuario no debería necesitar invocar manualmente a cada especialista.

Ejemplos:

```text
/project-review full
/project-review security
/project-review architecture,qa
/project-review --diff main
/project-review pre-release
```

La sesión principal o adaptador actúa como orquestador.

## 1.2. Especialistas, no un agente generalista

Cada agente debe tener:

- Un dominio definido
- Un checklist propio
- Herramientas restringidas
- Contexto controlado
- Formato de salida común
- Criterios de calidad
- Límites claros de responsabilidad

Más agentes no implican automáticamente mejor análisis. Si varios agentes reciben el mismo prompt genérico, solo producen opiniones repetidas con nombres diferentes.

## 1.3. Evidencia antes que opinión

Todo hallazgo debe incluir:

- Archivos y líneas
- Evidencia técnica
- Impacto
- Supuestos
- Información faltante
- Confianza
- Clasificación
- Recomendación proporcional

No debe presentarse una preferencia arquitectónica como defecto ni una falta de documentación como vulnerabilidad.

## 1.4. Herramientas deterministas antes que inferencia

Los agentes interpretan. Las herramientas deterministas comprueban.

Antes del análisis con LLM, CodeCouncil debe identificar o ejecutar, cuando corresponda:

- Linters
- Tests
- Type checking
- Cobertura
- SAST
- SCA
- Secret scanning
- IaC scanning
- Container scanning
- SBOM
- Análisis de complejidad
- Validación de OpenAPI
- Accessibility testing
- Benchmarking básico

## 1.5. Incertidumbre explícita

CodeCouncil debe distinguir entre:

- Hallazgo confirmado
- Riesgo probable
- Debilidad de diseño
- Brecha de documentación
- Brecha de pruebas
- Mejora
- Evidencia insuficiente

## 1.6. Causas raíz, no síntomas aislados

El consolidador debe fusionar hallazgos relacionados y evitar tickets duplicados.

Ejemplo:

- QA detecta falta de pruebas de revocación concurrente
- Arquitectura detecta inconsistencia entre caché y permisos
- Seguridad detecta acceso persistente después de revocación

El resultado debería ser un único finding consolidado sobre la causa raíz.

---

# 2. Arquitectura general

```text
Repositorio + documentación + CI/CD + infraestructura + requisitos
                             │
                             ▼
                  Recolector de contexto
                             │
                             ▼
                  Mapa común del proyecto
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   Arquitectura          Desarrollo           Seguridad
        ▼                    ▼                    ▼
       QA                   SRE                 UX
        └────────────────────┼────────────────────┘
                             ▼
                    Findings Challenger
                             ▼
                  Report Consolidator
                             ▼
              Reporte + backlog + evidencia
```

## Componentes principales

| Componente | Responsabilidad |
|---|---|
| Skill `/project-review` | Punto de entrada para el usuario |
| Orquestador principal | Coordina la ejecución |
| Project Discovery | Construye el mapa del proyecto |
| Evidence Collector | Ejecuta herramientas y normaliza resultados |
| Specialist Agents | Analizan dominios específicos |
| Findings Challenger | Refuta, valida o ajusta hallazgos |
| Cross-domain Analyzer | Detecta contradicciones entre disciplinas |
| Report Consolidator | Deduplica, prioriza y genera entregables |
| Hooks | Automatizan controles deterministas |
| Plugin/Adapter | Empaqueta la experiencia para cada coding agent |

---

# 3. Estado del MVP

El MVP inicial de CodeCouncil incluía:

1. Project Discovery
2. Software Architect
3. Senior Developer
4. QA Reviewer
5. AppSec Reviewer
6. Findings Challenger
7. Report Consolidator

También incluía:

- Núcleo independiente del proveedor
- Adaptador inicial para Claude Code
- Esquemas de salida
- Modos full, focalizado y diff
- Reportes Markdown y JSON
- Restricción de solo lectura
- Validación de findings
- Consolidación básica

El siguiente paso no debería ser agregar agentes indiscriminadamente. Primero debe validarse que el MVP produzca resultados correctos, diferenciados y accionables.

---

# 4. Fase prioritaria: evaluación de calidad

## 4.1. Objetivo

Comprobar que CodeCouncil:

- Encuentra problemas reales
- Evita falsos positivos
- No infla severidades
- No repite findings
- No presenta recomendaciones genéricas
- Declara cuando no tiene evidencia
- Produce resultados relativamente consistentes

## 4.2. Repositorios de evaluación

Crear un banco de pruebas:

```text
tests/evaluation/
├── vulnerable-project/
├── healthy-project/
├── ambiguous-project/
├── architecture-smells/
├── qa-gaps/
└── authorization-flaws/
```

### Vulnerable project

Debe contener defectos conocidos y documentados.

Ejemplos:

- Bypass de autorización
- Validación tardía
- Secretos en logs
- Retry no idempotente
- Migración sin rollback
- Falta de tests en flujo crítico

### Healthy project

Debe contener implementaciones correctas que no deberían marcarse.

Su objetivo es medir falsos positivos.

### Ambiguous project

Debe contener situaciones en las que falte contexto.

CodeCouncil debería responder con:

- Riesgo probable
- Confianza baja o media
- Información faltante
- Necesidad de validación adicional

No debería afirmar un defecto crítico.

## 4.3. Métricas

```text
precision = hallazgos válidos / hallazgos totales

recall = defectos conocidos detectados / defectos conocidos

duplicate_rate

unsupported_claim_rate

severity_accuracy

run_to_run_consistency

actionability_rate

human_acceptance_rate
```

## 4.4. Pregunta central

CodeCouncil debe poder demostrar que es mejor que:

- Ejecutar cuatro prompts separados
- Usar un único agente generalista
- Ejecutar únicamente herramientas estáticas
- Generar un reporte sin verificación crítica

---

# 5. Nuevos especialistas

## 5.1. SRE Reviewer

### Objetivo

Evaluar operabilidad, resiliencia y preparación para producción.

### Áreas

- Logs estructurados
- Métricas
- Traces
- Correlation IDs
- Health checks
- Readiness y liveness
- Timeouts
- Retries
- Circuit breakers
- Backpressure
- Graceful shutdown
- Autoscaling
- Capacidad
- Rollback
- Feature flags
- Backups
- Disaster recovery
- Runbooks
- SLI y SLO
- Gestión de configuración
- Separación de ambientes
- Infraestructura como código
- Migraciones de base de datos
- Diagnóstico de incidentes

### Restricción

Debe diferenciar entre:

```text
configuración observable en el repositorio
capacidad inferida
evidencia real de producción
```

No puede afirmar que una aplicación no es observable solo porque no encuentra una integración específica en el código.

---

## 5.2. UX y Accessibility Reviewer

### Condiciones de activación

Solo debe ejecutarse cuando exista evidencia suficiente:

- Frontend
- Aplicación ejecutable
- Storybook
- Screenshots
- Diseños
- Figma
- Flujos
- Tests end-to-end

### Áreas

- Navegación
- Jerarquía visual
- Formularios
- Estados de error
- Estados vacíos
- Estados de carga
- Prevención de errores
- Recuperación
- Acciones destructivas
- Responsive
- Teclado
- Semántica HTML
- Lectores de pantalla
- Contraste
- Microcopy
- Consistencia
- Percepción de rendimiento
- Flujo seguro y usable

### División futura

```text
UX técnico y accesibilidad
UX de producto
```

El segundo requiere más evidencia:

- Analytics
- Entrevistas
- Investigación de usuarios
- Métricas
- Objetivos de negocio

---

## 5.3. Product Reviewer

### Objetivo

Evaluar si el sistema resuelve el problema correcto y si las reglas de negocio están completas.

### Áreas

- Requisitos ambiguos
- Requisitos contradictorios
- Reglas implícitas
- Flujos incompletos
- Casos excepcionales
- Funcionalidad sin métrica de éxito
- Complejidad técnica sin valor demostrado
- Desalineación entre código y producto
- Métricas de adopción
- Telemetría funcional
- Funciones sin uso evidente

### Evidencia necesaria

- PRD
- Historias de usuario
- Tickets
- Criterios de aceptación
- Documentación funcional
- Roadmap
- Métricas

---

## 5.4. API Design Reviewer

### Áreas

- Semántica HTTP
- Recursos
- Naming
- Versionado
- Paginación
- Idempotencia
- Códigos de respuesta
- Manejo de errores
- Compatibilidad
- OpenAPI
- Webhooks
- Rate limits
- Filtros
- Trazabilidad
- Contratos
- Evolución de esquemas

### Valor

Este agente debe diferenciar:

- Defecto del contrato
- Breaking change
- Inconsistencia
- Mejora de diseño
- Preferencia estilística

---

## 5.5. Privacy and Data Governance Reviewer

### Áreas

- Clasificación de datos
- Minimización
- Retención
- Eliminación
- Lineage
- Datos personales
- Datos sensibles en logs
- Cifrado
- Control de acceso
- Datos de producción en pruebas
- Anonimización
- Consentimiento
- Exportación
- Derecho de eliminación
- Integridad
- Localización de datos

---

## 5.6. FinOps Reviewer

### Áreas

- Recursos sobredimensionados
- Recursos ociosos
- Autoscaling
- Retención excesiva
- Egress
- Servicios premium innecesarios
- Logs de alta cardinalidad
- Queries costosas
- Costos por ambiente
- Budgets
- Alertas
- Costos unitarios
- Capacidad reservada
- Optimización de almacenamiento

### Restricción

Sin telemetría o facturación real, los findings deben presentarse como hipótesis de optimización, no como ahorros demostrados.

---

## 5.7. AI Security Reviewer

### Áreas

- Prompt injection
- Indirect prompt injection
- Tool abuse
- Exposición de datos
- Autorización de herramientas
- Acceso excesivo
- Supply chain de modelos
- RAG poisoning
- Instrucciones no confiables
- Data leakage
- Jailbreaks
- Escalación de acciones
- Logging de información sensible
- Control de ejecución

---

## 5.8. AI Quality and Evaluation Reviewer

### Áreas

- Evaluaciones
- Datasets
- Ground truth
- Alucinaciones
- Latencia
- Costos
- Fallbacks
- Model routing
- Consistencia
- Reproducibilidad
- Observabilidad
- Calidad de respuestas
- Tasa de rechazo
- Tasa de corrección humana
- Sesgos
- Drift

---

# 6. Selección dinámica de especialistas

CodeCouncil debe elegir revisores según:

- Modo solicitado
- Stack
- Tipo de aplicación
- Archivos detectados
- Interfaces
- Evidencia disponible
- Criticidad
- Perfil seleccionado

Ejemplo:

```yaml
detected:
  frontend: true
  terraform: true
  openapi: true
  kubernetes: false
  llm_usage: false
  production_telemetry: false

selected:
  - architecture
  - developer
  - qa
  - security
  - ux-accessibility
  - sre
  - api-design
  - finops

skipped:
  ai-review:
    reason: No AI components detected

  production-reliability:
    reason: No production telemetry available
```

Debe declarar el nivel posible de análisis:

```text
SRE readiness: completo
SRE production behavior: no evaluable
UX accessibility: completo
UX product effectiveness: limitado
FinOps architecture review: disponible
FinOps savings estimate: no disponible
```

---

# 7. Perfiles de revisión

Además de los modos básicos, CodeCouncil debe soportar perfiles orientados a situaciones reales.

```text
/project-review pre-release
/project-review new-api
/project-review cloud-migration
/project-review incident-readiness
/project-review onboarding
/project-review legacy-modernization
/project-review compliance-readiness
/project-review performance
/project-review dependency-upgrade
/project-review architecture-change
```

## Ejemplo: pre-release

```yaml
profiles:
  pre-release:
    specialists:
      - qa
      - security
      - sre
      - api-design

    focus:
      - regressions
      - breaking_changes
      - deployment_risk
      - rollback
      - critical_vulnerabilities
```

## Ejemplo: cloud-migration

```yaml
profiles:
  cloud-migration:
    specialists:
      - architecture
      - security
      - sre
      - finops
      - privacy

    focus:
      - identity
      - networking
      - data_migration
      - resilience
      - rollback
      - cost
      - compliance
```

---

# 8. Revisión incremental inteligente

El modo diff no debe limitarse a las líneas cambiadas.

Debe construir un grafo de impacto:

```text
archivo modificado
    ↓
módulo afectado
    ↓
interfaces públicas
    ↓
consumidores
    ↓
tests relacionados
    ↓
riesgos transversales
```

Ejemplo:

```text
Se modificó PermissionService
→ afecta SecretController
→ afecta share-secret y revoke-access
→ afecta caché de autorización
→ requiere pruebas de integración y concurrencia
```

## Capacidades futuras

- Dependencias estáticas
- Call graph
- Import graph
- Service graph
- Test mapping
- Ownership mapping
- API consumers
- Database tables affected
- Event consumers
- Infrastructure dependencies

---

# 9. Integraciones con el ciclo de desarrollo

## 9.1. GitHub y GitLab

- Resumen en pull request o merge request
- Findings inline
- Quality gate
- Estado de pipeline
- Comparación contra baseline
- Nuevos findings
- Findings resueltos
- Links a evidencia
- Comentarios por dominio
- Resumen ejecutivo

## 9.2. Issues

Integraciones futuras:

- Jira
- GitHub Issues
- GitLab Issues
- Azure DevOps

Regla:

No crear un ticket por cada finding bruto. Primero se deben consolidar duplicados y causas raíz.

## 9.3. Formatos interoperables

- SARIF
- JUnit XML
- CycloneDX
- CSV
- HTML
- JSON estable
- Markdown
- JSON Lines para procesamiento masivo

## 9.4. PR asistidos

Flujo futuro:

```text
finding confirmado
    ↓
plan de corrección
    ↓
propuesta de cambios
    ↓
tests
    ↓
PR
    ↓
revisión humana
```

No habilitar merge automático en las primeras etapas.

---

# 10. Baselines y gestión del ruido

## 10.1. Baseline

```text
.codecouncil/baseline.json
```

Debe distinguir:

- Findings existentes
- Findings nuevos
- Findings resueltos
- Findings reintroducidos
- Riesgos aceptados
- Falsos positivos
- Findings expirados
- Findings sin owner

## 10.2. Comandos

```text
/project-review --baseline
/project-review --new-findings-only
/project-review --update-baseline
/project-review --compare-baseline
```

## 10.3. Supresiones

```yaml
suppressions:
  - finding_id: CC-SEC-014
    reason: Mitigated by API Gateway policy
    evidence: docs/security/api-gateway-policy.md
    expires: 2026-12-31
    owner: platform-security
```

Las supresiones deben:

- Tener justificación
- Tener evidencia
- Tener owner
- Tener fecha de expiración
- Poder revisarse

---

# 11. Challenger avanzado

## Flujo de debate

```text
Especialista presenta finding
        ↓
Challenger intenta refutarlo
        ↓
Especialista responde con evidencia adicional
        ↓
Judge decide
```

No se recomienda usar este debate completo para todos los findings.

Debe reservarse para:

- Critical
- High
- Baja confianza
- Findings contradictorios
- Findings que bloquean release
- Findings con fuerte impacto de negocio

## Challengers especializados

```text
Security Exploitability Challenger
Architecture Trade-off Challenger
QA Test Adequacy Challenger
SRE Operability Challenger
Privacy Evidence Challenger
```

---

# 12. Contradicciones entre dominios

CodeCouncil debe detectar conflictos como:

- SRE propone más logging; seguridad detecta secretos
- UX propone sesiones persistentes; seguridad propone expiración corta
- Developer propone caché; arquitectura detecta inconsistencia
- Seguridad agrega fricción; UX detecta bypass probable
- QA propone mocks; arquitectura advierte pérdida de realismo
- FinOps recomienda menor redundancia; SRE detecta pérdida de resiliencia
- Privacy recomienda menor retención; Product solicita analytics históricos

## Ejemplo de salida

```markdown
## Cross-domain trade-offs

### Session duration

Security:
Reducir sesión a 10 minutos.

UX:
Una sesión de 10 minutos interrumpe el flujo principal.

Recommendation:
Usar sesión corta con refresh token rotativo y reautenticación
solo para acciones sensibles.
```

---

# 13. Seguridad del propio CodeCouncil

El repositorio analizado debe tratarse como entrada hostil.

## Riesgos

- Prompt injection en README
- Prompt injection en comentarios
- Instrucciones en archivos de configuración
- Issues exportados maliciosos
- Resultados manipulados
- Scripts peligrosos
- Symlinks fuera del repositorio
- Submódulos no confiables
- Archivos enormes
- Binarios
- Secretos
- Exfiltración por red
- Comandos destructivos
- Dependencias maliciosas

## Controles

- Workspace de solo lectura
- Sin red por defecto
- Allowlist de comandos
- Límites de CPU
- Límites de memoria
- Timeouts
- Redacción de secretos
- Bloqueo de symlinks externos
- Registro de comandos
- Aislamiento por contenedor
- Sin credenciales
- Validación de salida
- Escaneo de instrucciones maliciosas
- Separación entre datos y órdenes

## Arquitectura segura

```text
CodeCouncil
    ↓
workspace de solo lectura
    ↓
contenedor sin credenciales
    ↓
sin acceso de red por defecto
    ↓
resultados normalizados
```

---

# 14. Rendimiento, costos y reproducibilidad

## Capacidades

- Cachear project-context
- Cachear resultados por commit
- No releer archivos sin cambios
- Limitar contexto por agente
- Resumir archivos grandes
- Ejecutar especialistas en paralelo
- Presupuesto de tokens
- Presupuesto de tiempo
- Model routing
- Modelos diferentes por dominio
- Persistir versión de prompts
- Generar run ID
- Registrar configuración
- Registrar commit
- Registrar versión de CodeCouncil

## Ejemplo

```json
{
  "run_id": "cc-20260612-a81f",
  "commit": "83d92bc",
  "profile": "pre-release",
  "codecouncil_version": "0.3.0",
  "specialists": {
    "security": {
      "model": "configured-model",
      "prompt_version": "2.1.0"
    }
  }
}
```

La reproducibilidad debe permitir distinguir si un cambio provino de:

- Código
- Prompt
- Modelo
- Configuración
- Herramienta
- Perfil
- Evidencia

---

# 15. Adaptadores

Arquitectura prevista:

```text
adapters/
├── claude-code/
├── codex/
├── cursor/
├── github-copilot/
└── generic-cli/
```

## Orden recomendado

1. Claude Code
2. CLI genérico
3. Codex
4. Cursor
5. GitHub Copilot

## CLI genérico

Ejemplo:

```bash
codecouncil review \
  --profile pre-release \
  --output .codecouncil \
  --fail-on critical
```

El CLI es clave para CI/CD y automatización sin depender de la interfaz de un coding agent.

---

# 16. Distribución

## Separación de repositorios

```text
codecouncil = producto
appsec-plugins = catálogo y distribución
```

CodeCouncil debe tener:

- Repositorio propio
- Releases
- Tags
- Changelog
- Tests
- Roadmap
- Documentación
- Artefactos

`appsec-plugins` debe:

- Publicar o referenciar versiones
- Instalar releases
- Mantener metadatos
- Verificar checksums
- Evitar duplicar el core

## Ejemplo

```yaml
name: codecouncil
version: 0.4.0
channel: stable
artifact: codecouncil-claude-code-v0.4.0.tar.gz
checksum: sha256:...
```

## Canales

- Experimental
- Beta
- Stable
- LTS, si en el futuro aplica

---

# 17. Remediación asistida

## Etapas

1. Plan de corrección
2. Issue
3. Propuesta de patch
4. Tests
5. Pull request
6. Revisión humana
7. Verificación posterior

## Reglas

- No modificar sin aprobación
- No corregir findings con baja confianza
- Incluir tests
- Mantener trazabilidad
- Relacionar PR con finding
- Verificar que el riesgo desapareció
- Evitar cambios masivos automáticos
- No hacer merge automático inicialmente

---

# 18. Telemetría y aprendizaje

CodeCouncil debería medir su propio desempeño.

## Métricas

- Findings por dominio
- Findings aceptados
- Findings rechazados
- Falsos positivos
- Severidades ajustadas
- Findings fusionados
- Tiempo por agente
- Tokens por agente
- Costos
- Tiempo hasta remediación
- Findings reintroducidos
- Calidad por prompt version
- Calidad por modelo
- Valoración humana

## Feedback

El usuario debería poder marcar:

```text
valid
invalid
duplicate
not-actionable
accepted-risk
fixed
needs-more-evidence
```

Ese feedback puede utilizarse para mejorar:

- Prompts
- Checklists
- Priorización
- Selección de agentes
- Reglas de challenger
- Model routing

---

# 19. Gobernanza

## Versionado

- Versionar prompts
- Versionar schemas
- Versionar checklists
- Versionar perfiles
- Versionar adaptadores
- Mantener compatibilidad

## Ownership

Cada especialista debería tener:

- Owner
- Maintainers
- Changelog
- Tests
- Casos de evaluación
- Política de cambios

## Revisión de cambios

Cambios en prompts o severidades deben pasar por:

- Evaluación
- Comparación contra baseline
- Revisión humana
- Pruebas de regresión

---

# 20. Roadmap por etapas

## Etapa 1: Calidad

1. Evaluation harness
2. Repositorios fixture
3. Métricas
4. Tests de regresión de prompts
5. Consistencia entre ejecuciones
6. Matriz de falsos positivos
7. Validación humana
8. Comparación contra prompts separados

## Etapa 2: Adopción real

1. Baselines
2. Nuevos findings solamente
3. Modo CI
4. SARIF
5. Comentarios en merge requests
6. Integración con appsec-plugins
7. Artefactos versionados
8. Changelog
9. Canal stable

## Etapa 3: Profundidad

1. SRE Reviewer
2. API Design Reviewer
3. UX/Accessibility Reviewer
4. Privacy Reviewer
5. Product Reviewer
6. FinOps Reviewer
7. AI Security Reviewer
8. AI Quality Reviewer

## Etapa 4: Inteligencia

1. Grafo de impacto
2. Contradicciones entre dominios
3. Debate selectivo
4. Agrupación por causa raíz
5. Priorización por riesgo y esfuerzo
6. Model routing
7. Selección dinámica avanzada
8. Scoring de confianza

## Etapa 5: Remediación asistida

1. Planes de corrección
2. Issues
3. Propuestas de patch
4. Tests
5. Pull requests
6. Verificación posterior
7. Cierre automático de findings verificados
8. Seguimiento de reintroducciones

---

# 21. Prioridad recomendada actual

Antes de agregar más agentes:

1. Construir el banco de evaluación
2. Definir defectos conocidos
3. Medir precision y falsos positivos
4. Evaluar consistencia
5. Probar Architecture, Developer, QA y AppSec
6. Verificar que cada uno aporta una perspectiva diferente
7. Mejorar el Challenger
8. Crear baseline
9. Integrar con CI
10. Agregar SRE y API Design

La secuencia recomendada es:

```text
Calidad
  ↓
Adopción
  ↓
Profundidad
  ↓
Inteligencia
  ↓
Remediación
```

No debe invertirse.

Agregar muchos agentes antes de validar la calidad solo aumenta la cantidad de texto, los costos y los falsos positivos.

---

# 22. Criterios de éxito

CodeCouncil será útil cuando pueda demostrar que:

- Encuentra problemas reales
- Explica por qué importan
- Cita evidencia
- Declara incertidumbre
- Reduce duplicados
- Prioriza correctamente
- Detecta trade-offs
- Produce un backlog accionable
- Se integra al flujo de desarrollo
- Mantiene consistencia
- No modifica código sin aprobación
- Puede verificarse y auditarse
- Mejora con feedback

El objetivo final no es reemplazar arquitectos, developers, QA, AppSec, SRE o UX.

El objetivo es convertir sus perspectivas en un proceso repetible, trazable y accesible desde el flujo normal de desarrollo.

---

# 23. Resumen ejecutivo

CodeCouncil debe evolucionar desde un orquestador básico hacia una plataforma de revisión de ingeniería.

La prioridad inmediata es validar el MVP con repositorios de evaluación y métricas objetivas.

Después debe incorporar:

- Baselines
- CI/CD
- Integraciones
- Nuevos especialistas
- Grafo de impacto
- Debate entre agentes
- Contradicciones entre dominios
- Remediación asistida

La regla rectora debe mantenerse:

> Evidencia antes que opinión, calidad antes que cantidad y causas raíz antes que síntomas.
