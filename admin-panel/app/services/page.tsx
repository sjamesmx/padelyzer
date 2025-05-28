"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Server, Cpu, MemoryStick, HardDrive, RefreshCw, Play, Pause, RotateCcw } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const mockServices = [
  {
    name: "Video Processing API",
    description: "Servicio principal de procesamiento de video",
    status: "online",
    latency: 45,
    version: "v2.1.3",
    lastUpdate: "2024-01-20 10:30",
    endpoints: ["/api/v1/process", "/api/v1/status"],
    resources: { cpu: 65, memory: 78, disk: 45 },
    workers: 8,
    queue: 23,
    errors: 2,
  },
  {
    name: "User Management API",
    description: "Gestión de usuarios y autenticación",
    status: "online",
    latency: 12,
    version: "v1.8.2",
    lastUpdate: "2024-01-19 16:45",
    endpoints: ["/api/v1/users", "/api/v1/auth"],
    resources: { cpu: 25, memory: 45, disk: 30 },
    workers: 4,
    queue: 0,
    errors: 0,
  },
  {
    name: "Analytics Service",
    description: "Procesamiento de métricas y estadísticas",
    status: "offline",
    latency: 0,
    version: "v1.5.1",
    lastUpdate: "2024-01-18 14:20",
    endpoints: ["/api/v1/analytics", "/api/v1/metrics"],
    resources: { cpu: 0, memory: 0, disk: 60 },
    workers: 0,
    queue: 15,
    errors: 5,
  },
  {
    name: "Notification Service",
    description: "Envío de notificaciones y emails",
    status: "online",
    latency: 8,
    version: "v1.2.4",
    lastUpdate: "2024-01-20 09:15",
    endpoints: ["/api/v1/notifications", "/api/v1/email"],
    resources: { cpu: 15, memory: 32, disk: 25 },
    workers: 2,
    queue: 5,
    errors: 1,
  },
]

const mockLogs = [
  {
    timestamp: "2024-01-20 15:30:45",
    service: "Video Processing API",
    level: "ERROR",
    message: "Failed to process frame 1250 in video PL-002",
    details: "Memory allocation failed during frame processing",
  },
  {
    timestamp: "2024-01-20 15:28:12",
    service: "Analytics Service",
    level: "CRITICAL",
    message: "Service crashed during metrics calculation",
    details: "Unhandled exception in analytics pipeline",
  },
  {
    timestamp: "2024-01-20 15:25:33",
    service: "User Management API",
    level: "INFO",
    message: "User authentication successful",
    details: "User juan.perez@email.com logged in successfully",
  },
]

export default function ServicesPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Monitoreo de Servicios</h1>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <RefreshCw className="mr-2 h-4 w-4" />
                Actualizar
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Service Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Servicios Online</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3/4</div>
                <p className="text-xs text-muted-foreground">75% disponibilidad</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Workers Activos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">14</div>
                <p className="text-xs text-muted-foreground">8 procesando</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Cola Total</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">43</div>
                <p className="text-xs text-muted-foreground">tareas pendientes</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Errores (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">8</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-red-600">+3</span> vs. ayer
                </p>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="services" className="space-y-4">
            <TabsList>
              <TabsTrigger value="services">Servicios</TabsTrigger>
              <TabsTrigger value="resources">Recursos</TabsTrigger>
              <TabsTrigger value="logs">Logs Recientes</TabsTrigger>
            </TabsList>

            <TabsContent value="services" className="space-y-4">
              <div className="grid gap-4">
                {mockServices.map((service, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                              service.status === "online" ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"
                            }`}
                          >
                            <Server className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle className="text-base">{service.name}</CardTitle>
                            <CardDescription>{service.description}</CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={service.status === "online" ? "default" : "destructive"}>
                            {service.status === "online" ? "Online" : "Offline"}
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              alert(
                                `${service.status === "online" ? "Pausando" : "Iniciando"} servicio: ${service.name}`,
                              )
                            }
                          >
                            {service.status === "online" ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => alert(`Reiniciando servicio: ${service.name}`)}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-3">
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Latencia:</span>
                            <span className="font-semibold">{service.latency}ms</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Versión:</span>
                            <span className="font-semibold">{service.version}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Actualizado:</span>
                            <span className="font-semibold">{service.lastUpdate}</span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Workers:</span>
                            <span className="font-semibold">{service.workers}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Cola:</span>
                            <span className="font-semibold">{service.queue}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span>Errores:</span>
                            <span className={`font-semibold ${service.errors > 0 ? "text-red-600" : "text-green-600"}`}>
                              {service.errors}
                            </span>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="text-sm">
                            <div className="flex justify-between mb-1">
                              <span>CPU:</span>
                              <span>{service.resources.cpu}%</span>
                            </div>
                            <Progress value={service.resources.cpu} className="h-2" />
                          </div>
                          <div className="text-sm">
                            <div className="flex justify-between mb-1">
                              <span>Memoria:</span>
                              <span>{service.resources.memory}%</span>
                            </div>
                            <Progress value={service.resources.memory} className="h-2" />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="resources" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Cpu className="h-5 w-5" />
                      CPU Global
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">52%</div>
                    <Progress value={52} className="mt-2" />
                    <p className="text-xs text-muted-foreground mt-2">Promedio de todos los servicios</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MemoryStick className="h-5 w-5" />
                      Memoria Global
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">64%</div>
                    <Progress value={64} className="mt-2" />
                    <p className="text-xs text-muted-foreground mt-2">8.2GB / 12.8GB utilizados</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HardDrive className="h-5 w-5" />
                      Almacenamiento
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">78%</div>
                    <Progress value={78} className="mt-2" />
                    <p className="text-xs text-muted-foreground mt-2">156GB / 200GB utilizados</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Logs Recientes del Sistema</CardTitle>
                  <CardDescription>Últimos eventos y errores de los microservicios</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Servicio</TableHead>
                        <TableHead>Nivel</TableHead>
                        <TableHead>Mensaje</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockLogs.map((log, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono text-sm">{log.timestamp}</TableCell>
                          <TableCell>{log.service}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                log.level === "ERROR"
                                  ? "destructive"
                                  : log.level === "CRITICAL"
                                    ? "destructive"
                                    : "secondary"
                              }
                            >
                              {log.level}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-md truncate">{log.message}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">
                              Ver Detalles
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
