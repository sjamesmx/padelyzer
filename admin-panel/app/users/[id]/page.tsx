"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { ArrowLeft, Save, RotateCcw, Mail, TrendingUp, Video } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"
import Link from "next/link"

const mockUser = {
  id: 1,
  email: "juan.perez@email.com",
  name: "Juan Pérez",
  role: "Premium",
  status: "Activo",
  registrationDate: "2024-01-15",
  lastActivity: "2024-01-20",
  emailVerified: true,
  padelIQ: {
    score: 1247,
    level: "Avanzado",
    evolution: [
      { date: "2024-01-01", score: 1180 },
      { date: "2024-01-08", score: 1205 },
      { date: "2024-01-15", score: 1230 },
      { date: "2024-01-20", score: 1247 },
    ],
    metrics: {
      precision: 85,
      power: 78,
      strategy: 92,
      consistency: 88,
    },
  },
  analyses: [
    {
      id: "AN-001",
      date: "2024-01-20",
      type: "Partido",
      status: "Completado",
      duration: "45m",
      metrics: { precision: 87, power: 82, rallies: 156 },
    },
    {
      id: "AN-002",
      date: "2024-01-18",
      type: "Entrenamiento",
      status: "Completado",
      duration: "30m",
      metrics: { precision: 83, power: 75, rallies: 89 },
    },
    {
      id: "AN-003",
      date: "2024-01-15",
      type: "Partido",
      status: "Completado",
      duration: "52m",
      metrics: { precision: 85, power: 80, rallies: 203 },
    },
  ],
}

export default function UserEditPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-2">
              <Link href="/users">
                <Button variant="ghost" size="icon">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <h1 className="text-lg font-semibold">Editar Usuario - {mockUser.name}</h1>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          <Tabs defaultValue="profile" className="space-y-4">
            <TabsList>
              <TabsTrigger value="profile">Perfil</TabsTrigger>
              <TabsTrigger value="padeliq">Padel IQ</TabsTrigger>
              <TabsTrigger value="analyses">Análisis</TabsTrigger>
            </TabsList>

            <TabsContent value="profile" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Información del Usuario</CardTitle>
                  <CardDescription>Datos personales y configuración de cuenta</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Nombre Completo</Label>
                      <Input id="name" defaultValue={mockUser.name} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" type="email" defaultValue={mockUser.email} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">Rol</Label>
                      <Select defaultValue={mockUser.role}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Usuario">Usuario</SelectItem>
                          <SelectItem value="Premium">Premium</SelectItem>
                          <SelectItem value="Admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="status">Estado</Label>
                      <Select defaultValue={mockUser.status}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Activo">Activo</SelectItem>
                          <SelectItem value="Inactivo">Inactivo</SelectItem>
                          <SelectItem value="Suspendido">Suspendido</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Fecha de Registro</Label>
                      <div className="text-sm text-muted-foreground">{mockUser.registrationDate}</div>
                    </div>
                    <div className="space-y-2">
                      <Label>Última Actividad</Label>
                      <div className="text-sm text-muted-foreground">{mockUser.lastActivity}</div>
                    </div>
                    <div className="space-y-2">
                      <Label>Email Verificado</Label>
                      <Badge variant={mockUser.emailVerified ? "default" : "destructive"}>
                        {mockUser.emailVerified ? "Verificado" : "Pendiente"}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button>
                      <Save className="mr-2 h-4 w-4" />
                      Guardar Cambios
                    </Button>
                    <Button variant="outline">
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Resetear Contraseña
                    </Button>
                    <Button variant="outline">
                      <Mail className="mr-2 h-4 w-4" />
                      Reenviar Verificación
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="padeliq" className="space-y-4">
              <div className="grid gap-6">
                {/* Sección principal del Padel IQ */}
                <Card className="border-2 border-primary/20">
                  <CardHeader className="bg-primary/5">
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <TrendingUp className="h-6 w-6 text-primary" />
                      Padel IQ Score
                    </CardTitle>
                    <CardDescription>Puntuación y nivel actual del jugador</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <div className="grid gap-6 md:grid-cols-3">
                      <div className="text-center">
                        <div className="text-4xl font-bold text-primary mb-2">{mockUser.padelIQ.score}</div>
                        <div className="text-lg font-semibold text-muted-foreground">{mockUser.padelIQ.level}</div>
                        <div className="text-sm text-muted-foreground mt-1">Puntuación actual</div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Precisión</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary h-2 rounded-full"
                                style={{ width: `${mockUser.padelIQ.metrics.precision}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-semibold w-10">{mockUser.padelIQ.metrics.precision}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Potencia</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary h-2 rounded-full"
                                style={{ width: `${mockUser.padelIQ.metrics.power}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-semibold w-10">{mockUser.padelIQ.metrics.power}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Estrategia</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary h-2 rounded-full"
                                style={{ width: `${mockUser.padelIQ.metrics.strategy}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-semibold w-10">{mockUser.padelIQ.metrics.strategy}%</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">Consistencia</span>
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-primary h-2 rounded-full"
                                style={{ width: `${mockUser.padelIQ.metrics.consistency}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-semibold w-10">{mockUser.padelIQ.metrics.consistency}%</span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-3">Evolución Reciente</h4>
                        <div className="space-y-2">
                          {mockUser.padelIQ.evolution.map((point, index) => (
                            <div key={index} className="flex justify-between items-center text-sm">
                              <span className="text-muted-foreground">{point.date}</span>
                              <span className="font-semibold">{point.score}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="analyses" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Video className="h-6 w-6" />
                    Videos Analizados
                  </CardTitle>
                  <CardDescription>Historial completo de análisis de video realizados</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Duración</TableHead>
                        <TableHead>Precisión</TableHead>
                        <TableHead>Potencia</TableHead>
                        <TableHead>Rallies</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockUser.analyses.map((analysis) => (
                        <TableRow key={analysis.id}>
                          <TableCell className="font-medium">{analysis.id}</TableCell>
                          <TableCell>{analysis.date}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{analysis.type}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="default">{analysis.status}</Badge>
                          </TableCell>
                          <TableCell>{analysis.duration}</TableCell>
                          <TableCell>{analysis.metrics.precision}%</TableCell>
                          <TableCell>{analysis.metrics.power}%</TableCell>
                          <TableCell>{analysis.metrics.rallies}</TableCell>
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
