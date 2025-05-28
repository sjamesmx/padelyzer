"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Shield, Users, Key, AlertTriangle, Eye, X, Plus, Edit } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const mockRoles = [
  {
    name: "Super Admin",
    description: "Acceso completo al sistema",
    users: 2,
    permissions: [
      "users.read",
      "users.write",
      "users.delete",
      "config.read",
      "config.write",
      "logs.read",
      "analytics.read",
    ],
  },
  {
    name: "Admin",
    description: "Administrador con permisos limitados",
    users: 5,
    permissions: ["users.read", "users.write", "config.read", "logs.read", "analytics.read"],
  },
  {
    name: "Moderator",
    description: "Moderador de contenido y usuarios",
    users: 12,
    permissions: ["users.read", "logs.read", "analytics.read"],
  },
  {
    name: "Premium",
    description: "Usuario premium con funciones avanzadas",
    users: 234,
    permissions: ["analysis.advanced", "export.unlimited", "priority.support"],
  },
  {
    name: "Usuario",
    description: "Usuario básico del sistema",
    users: 987,
    permissions: ["analysis.basic", "export.limited"],
  },
]

const mockSessions = [
  {
    user: "admin@padelyzer.com",
    ip: "192.168.1.100",
    location: "Madrid, España",
    device: "Chrome 120.0 - Windows",
    loginTime: "2024-01-20 14:30",
    lastActivity: "2024-01-20 15:45",
    status: "Activa",
  },
  {
    user: "juan.perez@email.com",
    ip: "10.0.0.50",
    location: "Barcelona, España",
    device: "Safari 17.0 - macOS",
    loginTime: "2024-01-20 13:15",
    lastActivity: "2024-01-20 15:42",
    status: "Activa",
  },
  {
    user: "maria.garcia@email.com",
    ip: "203.45.67.89",
    location: "Valencia, España",
    device: "Firefox 121.0 - Linux",
    loginTime: "2024-01-20 12:00",
    lastActivity: "2024-01-20 15:30",
    status: "Sospechosa",
  },
]

const mockApiKeys = [
  {
    name: "Mobile App API",
    key: "pk_live_51H7...",
    permissions: ["analysis.create", "users.read"],
    lastUsed: "2024-01-20 15:30",
    status: "Activa",
  },
  {
    name: "Analytics Dashboard",
    key: "pk_test_4B2...",
    permissions: ["analytics.read", "metrics.read"],
    lastUsed: "2024-01-20 14:15",
    status: "Activa",
  },
  {
    name: "Legacy Integration",
    key: "pk_live_3A1...",
    permissions: ["users.read"],
    lastUsed: "2024-01-18 10:30",
    status: "Inactiva",
  },
]

export default function SecurityPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Seguridad y Accesos</h1>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          <Tabs defaultValue="roles" className="space-y-4">
            <TabsList>
              <TabsTrigger value="roles">Roles y Permisos</TabsTrigger>
              <TabsTrigger value="sessions">Sesiones Activas</TabsTrigger>
              <TabsTrigger value="apikeys">API Keys</TabsTrigger>
              <TabsTrigger value="audit">Auditoría</TabsTrigger>
            </TabsList>

            <TabsContent value="roles" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Gestión de Roles
                      </CardTitle>
                      <CardDescription>Administra roles y permisos del sistema</CardDescription>
                    </div>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Nuevo Rol
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rol</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead>Usuarios</TableHead>
                        <TableHead>Permisos</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockRoles.map((role, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{role.name}</TableCell>
                          <TableCell>{role.description}</TableCell>
                          <TableCell>{role.users}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {role.permissions.slice(0, 3).map((permission) => (
                                <Badge key={permission} variant="outline" className="text-xs">
                                  {permission}
                                </Badge>
                              ))}
                              {role.permissions.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{role.permissions.length - 3} más
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button variant="ghost" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="sessions" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Sesiones Activas
                  </CardTitle>
                  <CardDescription>Monitorea y gestiona sesiones de usuario activas</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Usuario</TableHead>
                        <TableHead>IP</TableHead>
                        <TableHead>Ubicación</TableHead>
                        <TableHead>Dispositivo</TableHead>
                        <TableHead>Inicio de Sesión</TableHead>
                        <TableHead>Última Actividad</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockSessions.map((session, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{session.user}</TableCell>
                          <TableCell className="font-mono text-sm">{session.ip}</TableCell>
                          <TableCell>{session.location}</TableCell>
                          <TableCell>{session.device}</TableCell>
                          <TableCell>{session.loginTime}</TableCell>
                          <TableCell>{session.lastActivity}</TableCell>
                          <TableCell>
                            <Badge variant={session.status === "Sospechosa" ? "destructive" : "default"}>
                              {session.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm" className="text-red-600">
                              <X className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="apikeys" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Key className="h-5 w-5" />
                        API Keys
                      </CardTitle>
                      <CardDescription>Gestiona claves de API y tokens de acceso</CardDescription>
                    </div>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Nueva API Key
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nombre</TableHead>
                        <TableHead>Clave</TableHead>
                        <TableHead>Permisos</TableHead>
                        <TableHead>Último Uso</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockApiKeys.map((apiKey, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{apiKey.name}</TableCell>
                          <TableCell className="font-mono text-sm">{apiKey.key}</TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {apiKey.permissions.map((permission) => (
                                <Badge key={permission} variant="outline" className="text-xs">
                                  {permission}
                                </Badge>
                              ))}
                            </div>
                          </TableCell>
                          <TableCell>{apiKey.lastUsed}</TableCell>
                          <TableCell>
                            <Badge variant={apiKey.status === "Activa" ? "default" : "secondary"}>
                              {apiKey.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button variant="ghost" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" className="text-red-600">
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="audit" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Auditoría de Seguridad
                  </CardTitle>
                  <CardDescription>Configuración de alertas y monitoreo de seguridad</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Alertas de Login Sospechoso</Label>
                        <p className="text-xs text-muted-foreground">Notificar cuando se detecten accesos inusuales</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Monitoreo de Cambios de Rol</Label>
                        <p className="text-xs text-muted-foreground">
                          Alertar cuando se modifiquen permisos de usuario
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Detección de Fuerza Bruta</Label>
                        <p className="text-xs text-muted-foreground">Bloquear IPs con múltiples intentos fallidos</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Auditoría de API Keys</Label>
                        <p className="text-xs text-muted-foreground">Registrar todos los usos de API keys</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-4">
                    <div className="space-y-2">
                      <Label htmlFor="alert-email">Email para Alertas</Label>
                      <Input id="alert-email" defaultValue="security@padelyzer.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="retention-days">Retención de Logs (días)</Label>
                      <Input id="retention-days" type="number" defaultValue="90" min="30" />
                    </div>
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
