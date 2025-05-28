"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { ArrowLeft, Pause, Square, Download, RefreshCw, Clock, User, Video } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"
import Link from "next/link"

const mockPipeline = {
  id: "PL-002",
  user: "María García",
  userEmail: "maria.garcia@email.com",
  status: "En Proceso",
  progress: 65,
  type: "Entrenamiento",
  startTime: "2024-01-20 15:00",
  endTime: "-",
  duration: "8m",
  framesProcessed: 8100,
  totalFrames: 12500,
  currentStep: "Tracking",
  steps: [
    { name: "Subida", status: "Completado", duration: "30s", timestamp: "15:00:30" },
    { name: "Preprocesamiento", status: "Completado", duration: "2m", timestamp: "15:01:00" },
    { name: "Detección", status: "Completado", duration: "3m", timestamp: "15:04:00" },
    { name: "Tracking", status: "En Proceso", duration: "3m", timestamp: "15:07:00" },
    { name: "Análisis", status: "Pendiente", duration: "-", timestamp: "-" },
    { name: "Exportación", status: "Pendiente", duration: "-", timestamp: "-" },
  ],
  metrics: {
    detectedObjects: 1250,
    trackedPlayers: 2,
    rallies: 45,
    avgRallyDuration: 12.5,
  },
  logs: [
    { time: "15:07:45", level: "INFO", message: "Tracking player 1 at frame 8100" },
    { time: "15:07:30", level: "INFO", message: "Ball detected at coordinates (450, 320)" },
    { time: "15:07:15", level: "WARNING", message: "Temporary occlusion detected for player 2" },
    { time: "15:07:00", level: "INFO", message: "Starting tracking phase" },
  ],
}

export default function PipelineDetailPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-2">
              <Link href="/pipelines">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <h1 className="text-lg font-semibold">Análisis {mockPipeline.id}</h1>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Información general */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Usuario
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">{mockPipeline.user}</div>
                <div className="text-sm text-muted-foreground">{mockPipeline.userEmail}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Video className="h-4 w-4" />
                  Tipo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant="outline">{mockPipeline.type}</Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Duración
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">{mockPipeline.duration}</div>
                <div className="text-sm text-muted-foreground">Iniciado: {mockPipeline.startTime}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Estado</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant="secondary">{mockPipeline.status}</Badge>
                <div className="mt-2">
                  <Progress value={mockPipeline.progress} className="h-2" />
                  <div className="text-xs text-muted-foreground mt-1">{mockPipeline.progress}% completado</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Controles */}
          <Card>
            <CardHeader>
              <CardTitle>Controles de Pipeline</CardTitle>
              <CardDescription>Gestiona la ejecución del análisis</CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button variant="outline">
                <Pause className="mr-2 h-4 w-4" />
                Pausar
              </Button>
              <Button variant="outline">
                <Square className="mr-2 h-4 w-4" />
                Detener
              </Button>
              <Button variant="outline">
                <RefreshCw className="mr-2 h-4 w-4" />
                Reiniciar
              </Button>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Descargar Logs
              </Button>
            </CardContent>
          </Card>

          <Tabs defaultValue="progress" className="space-y-4">
            <TabsList>
              <TabsTrigger value="progress">Progreso</TabsTrigger>
              <TabsTrigger value="metrics">Métricas</TabsTrigger>
              <TabsTrigger value="logs">Logs</TabsTrigger>
            </TabsList>

            <TabsContent value="progress" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Pasos del Pipeline</CardTitle>
                  <CardDescription>Estado detallado de cada fase del análisis</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockPipeline.steps.map((step, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-3 h-3 rounded-full ${
                              step.status === "Completado"
                                ? "bg-green-500"
                                : step.status === "En Proceso"
                                  ? "bg-blue-500 animate-pulse"
                                  : "bg-gray-300"
                            }`}
                          />
                          <div>
                            <div className="font-medium">{step.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {step.timestamp !== "-" ? `Iniciado: ${step.timestamp}` : "Pendiente"}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge
                            variant={
                              step.status === "Completado"
                                ? "default"
                                : step.status === "En Proceso"
                                  ? "secondary"
                                  : "outline"
                            }
                          >
                            {step.status}
                          </Badge>
                          <div className="text-sm text-muted-foreground mt-1">
                            {step.duration !== "-" ? `Duración: ${step.duration}` : ""}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="metrics" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Detección</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span>Objetos detectados:</span>
                      <span className="font-semibold">{mockPipeline.metrics.detectedObjects.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Jugadores rastreados:</span>
                      <span className="font-semibold">{mockPipeline.metrics.trackedPlayers}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Análisis de Juego</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span>Rallies detectados:</span>
                      <span className="font-semibold">{mockPipeline.metrics.rallies}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Duración promedio:</span>
                      <span className="font-semibold">{mockPipeline.metrics.avgRallyDuration}s</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Progreso de Frames</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Frames procesados:</span>
                      <span>
                        {mockPipeline.framesProcessed.toLocaleString()} / {mockPipeline.totalFrames.toLocaleString()}
                      </span>
                    </div>
                    <Progress value={(mockPipeline.framesProcessed / mockPipeline.totalFrames) * 100} className="h-3" />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Logs del Análisis</CardTitle>
                  <CardDescription>Registro detallado de eventos durante el procesamiento</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {mockPipeline.logs.map((log, index) => (
                      <div key={index} className="flex items-start gap-3 p-2 border-l-2 border-l-gray-200">
                        <div className="text-xs text-muted-foreground font-mono">{log.time}</div>
                        <Badge
                          variant={
                            log.level === "ERROR" ? "destructive" : log.level === "WARNING" ? "secondary" : "outline"
                          }
                          className="text-xs"
                        >
                          {log.level}
                        </Badge>
                        <div className="text-sm flex-1">{log.message}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
