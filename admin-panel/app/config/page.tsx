"use client"

import { Badge } from "@/components/ui/badge"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Save, RotateCcw, Upload, Download, AlertTriangle, History } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const configHistory = [
  {
    date: "2024-01-20 14:30",
    user: "admin@padelyzer.com",
    change: "Actualizado umbral de detección de 0.75 a 0.80",
    section: "Análisis",
  },
  {
    date: "2024-01-19 16:45",
    user: "admin@padelyzer.com",
    change: "Configurado webhook para notificaciones",
    section: "Integraciones",
  },
  {
    date: "2024-01-18 10:15",
    user: "admin@padelyzer.com",
    change: "Aumentado límite de memoria por análisis a 4GB",
    section: "Recursos",
  },
]

export default function ConfigPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Configuración del Sistema</h1>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Upload className="mr-2 h-4 w-4" />
                Importar Config
              </Button>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Exportar Config
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          <Tabs defaultValue="analysis" className="space-y-4">
            <TabsList>
              <TabsTrigger value="analysis">Análisis</TabsTrigger>
              <TabsTrigger value="resources">Recursos</TabsTrigger>
              <TabsTrigger value="integrations">Integraciones</TabsTrigger>
              <TabsTrigger value="security">Seguridad</TabsTrigger>
              <TabsTrigger value="history">Historial</TabsTrigger>
            </TabsList>

            <TabsContent value="analysis" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Parámetros de Análisis</CardTitle>
                  <CardDescription>Configuración de umbrales y algoritmos de detección</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="detection-threshold">Umbral de Detección</Label>
                      <Input id="detection-threshold" type="number" defaultValue="0.80" step="0.01" min="0" max="1" />
                      <p className="text-xs text-muted-foreground">Confianza mínima para detección de objetos (0-1)</p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="tracking-threshold">Umbral de Tracking</Label>
                      <Input id="tracking-threshold" type="number" defaultValue="0.75" step="0.01" min="0" max="1" />
                      <p className="text-xs text-muted-foreground">Confianza mínima para seguimiento de objetos</p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="min-rally-duration">Duración Mínima de Rally (s)</Label>
                      <Input id="min-rally-duration" type="number" defaultValue="3" min="1" />
                      <p className="text-xs text-muted-foreground">Duración mínima para considerar un rally válido</p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="max-analysis-time">Tiempo Máximo de Análisis (min)</Label>
                      <Input id="max-analysis-time" type="number" defaultValue="60" min="10" />
                      <p className="text-xs text-muted-foreground">Tiempo límite antes de cancelar análisis</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Análisis de Biomecánica</Label>
                        <p className="text-xs text-muted-foreground">Activar análisis avanzado de movimientos</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Detección de Estrategias</Label>
                        <p className="text-xs text-muted-foreground">Analizar patrones de juego y estrategias</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Análisis de Emociones</Label>
                        <p className="text-xs text-muted-foreground">Detectar expresiones faciales y emociones</p>
                      </div>
                      <Switch />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="resources" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Límites de Recursos</CardTitle>
                  <CardDescription>Configuración de uso de CPU, memoria y almacenamiento</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="max-memory">Memoria Máxima por Análisis (GB)</Label>
                      <Input id="max-memory" type="number" defaultValue="4" min="1" max="16" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="max-cpu">CPU Máxima por Análisis (%)</Label>
                      <Input id="max-cpu" type="number" defaultValue="80" min="10" max="100" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="concurrent-analyses">Análisis Concurrentes</Label>
                      <Input id="concurrent-analyses" type="number" defaultValue="5" min="1" max="20" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="storage-limit">Límite de Almacenamiento (GB)</Label>
                      <Input id="storage-limit" type="number" defaultValue="500" min="100" />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="temp-storage">Ruta de Almacenamiento Temporal</Label>
                    <Input id="temp-storage" defaultValue="/tmp/padelyzer/processing" />
                    <p className="text-xs text-muted-foreground">
                      Directorio para archivos temporales durante el procesamiento
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="output-storage">Ruta de Almacenamiento de Resultados</Label>
                    <Input id="output-storage" defaultValue="/data/padelyzer/results" />
                    <p className="text-xs text-muted-foreground">Directorio para guardar resultados de análisis</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="integrations" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Webhooks y Notificaciones</CardTitle>
                  <CardDescription>Configuración de integraciones externas</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="webhook-url">URL de Webhook</Label>
                    <Input id="webhook-url" placeholder="https://api.ejemplo.com/webhook" />
                    <p className="text-xs text-muted-foreground">URL para recibir notificaciones de eventos</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="webhook-secret">Secret de Webhook</Label>
                    <Input id="webhook-secret" type="password" placeholder="••••••••••••••••" />
                    <p className="text-xs text-muted-foreground">Clave secreta para validar webhooks</p>
                  </div>

                  <div className="space-y-4">
                    <Label>Eventos a Notificar</Label>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Análisis Completado</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Error en Análisis</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Nuevo Usuario Registrado</Label>
                        <Switch />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Límite de Recursos Alcanzado</Label>
                        <Switch defaultChecked />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Configuración de Email</CardTitle>
                  <CardDescription>Parámetros para envío de notificaciones por email</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="smtp-host">Servidor SMTP</Label>
                      <Input id="smtp-host" defaultValue="smtp.gmail.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp-port">Puerto SMTP</Label>
                      <Input id="smtp-port" type="number" defaultValue="587" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp-user">Usuario SMTP</Label>
                      <Input id="smtp-user" defaultValue="noreply@padelyzer.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp-password">Contraseña SMTP</Label>
                      <Input id="smtp-password" type="password" placeholder="••••••••••••••••" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="security" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Configuración de Seguridad</CardTitle>
                  <CardDescription>Parámetros de autenticación y autorización</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="session-timeout">Timeout de Sesión (min)</Label>
                      <Input id="session-timeout" type="number" defaultValue="60" min="5" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="max-login-attempts">Intentos Máximos de Login</Label>
                      <Input id="max-login-attempts" type="number" defaultValue="5" min="3" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password-min-length">Longitud Mínima de Contraseña</Label>
                      <Input id="password-min-length" type="number" defaultValue="8" min="6" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lockout-duration">Duración de Bloqueo (min)</Label>
                      <Input id="lockout-duration" type="number" defaultValue="15" min="5" />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Autenticación de Dos Factores</Label>
                        <p className="text-xs text-muted-foreground">Requerir 2FA para usuarios admin</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Verificación de Email Obligatoria</Label>
                        <p className="text-xs text-muted-foreground">Los usuarios deben verificar su email</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Logging de Accesos</Label>
                        <p className="text-xs text-muted-foreground">Registrar todos los accesos al sistema</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="allowed-domains">Dominios Permitidos</Label>
                    <Textarea
                      id="allowed-domains"
                      placeholder="ejemplo.com&#10;empresa.com&#10;*.organizacion.com"
                      className="min-h-[100px]"
                    />
                    <p className="text-xs text-muted-foreground">
                      Lista de dominios permitidos para registro (uno por línea)
                    </p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    Historial de Cambios
                  </CardTitle>
                  <CardDescription>Auditoría de modificaciones en la configuración</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Sección</TableHead>
                        <TableHead>Cambio Realizado</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {configHistory.map((change, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono text-sm">{change.date}</TableCell>
                          <TableCell>{change.user}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{change.section}</Badge>
                          </TableCell>
                          <TableCell>{change.change}</TableCell>
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

          {/* Action Buttons */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <AlertTriangle className="h-4 w-4" />
                  Los cambios en la configuración pueden afectar el rendimiento del sistema
                </div>
                <div className="flex gap-2">
                  <Button variant="outline">
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Restaurar Defaults
                  </Button>
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Guardar Configuración
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
