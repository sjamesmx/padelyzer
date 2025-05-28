"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { TrendingUp, Users, Video, Clock, Download, RefreshCw } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const mockMetrics = {
  users: {
    total: 1234,
    active: 1156,
    new: 89,
    growth: 12.5,
  },
  analyses: {
    total: 2847,
    completed: 2756,
    inProgress: 23,
    failed: 68,
    avgTime: 4.2,
  },
  revenue: {
    monthly: 42350,
    yearly: 485200,
    growth: 8.3,
    churn: 5.8,
  },
  performance: {
    avgProcessingTime: 4.2,
    successRate: 96.8,
    systemUptime: 99.9,
    errorRate: 2.4,
  },
}

const weeklyData = [
  { day: "Lun", users: 45, analyses: 123, revenue: 1250 },
  { day: "Mar", users: 52, analyses: 145, revenue: 1420 },
  { day: "Mié", users: 38, analyses: 98, revenue: 980 },
  { day: "Jue", users: 61, analyses: 167, revenue: 1680 },
  { day: "Vie", users: 49, analyses: 134, revenue: 1340 },
  { day: "Sáb", users: 33, analyses: 89, revenue: 890 },
  { day: "Dom", users: 28, analyses: 76, revenue: 760 },
]

export default function MetricsPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Métricas y Reportes</h1>
            <div className="flex items-center gap-2">
              <Select defaultValue="7d">
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24h">24 horas</SelectItem>
                  <SelectItem value="7d">7 días</SelectItem>
                  <SelectItem value="30d">30 días</SelectItem>
                  <SelectItem value="90d">90 días</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm">
                <RefreshCw className="mr-2 h-4 w-4" />
                Actualizar
              </Button>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Exportar
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Resumen</TabsTrigger>
              <TabsTrigger value="users">Usuarios</TabsTrigger>
              <TabsTrigger value="analyses">Análisis</TabsTrigger>
              <TabsTrigger value="revenue">Ingresos</TabsTrigger>
              <TabsTrigger value="performance">Rendimiento</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              {/* Métricas principales */}
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Usuarios Totales</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockMetrics.users.total.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      <span className="text-green-600">+{mockMetrics.users.growth}%</span> vs. mes anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Análisis Completados</CardTitle>
                    <Video className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockMetrics.analyses.completed.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      Tasa de éxito: {mockMetrics.performance.successRate}%
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Ingresos Mensuales</CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">€{mockMetrics.revenue.monthly.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      <span className="text-green-600">+{mockMetrics.revenue.growth}%</span> vs. mes anterior
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Tiempo Promedio</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{mockMetrics.performance.avgProcessingTime}m</div>
                    <p className="text-xs text-muted-foreground">Por análisis de video</p>
                  </CardContent>
                </Card>
              </div>

              {/* Gráfico semanal */}
              <Card>
                <CardHeader>
                  <CardTitle>Actividad Semanal</CardTitle>
                  <CardDescription>Resumen de actividad de los últimos 7 días</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {weeklyData.map((day, index) => (
                      <div key={index} className="grid grid-cols-4 gap-4 items-center">
                        <div className="font-medium">{day.day}</div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Usuarios: </span>
                          <span className="font-semibold">{day.users}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Análisis: </span>
                          <span className="font-semibold">{day.analyses}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Ingresos: </span>
                          <span className="font-semibold">€{day.revenue}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="users" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Usuarios Activos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{mockMetrics.users.active.toLocaleString()}</div>
                    <p className="text-sm text-muted-foreground">
                      {((mockMetrics.users.active / mockMetrics.users.total) * 100).toFixed(1)}% del total
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Nuevos Usuarios</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{mockMetrics.users.new}</div>
                    <p className="text-sm text-muted-foreground">En los últimos 30 días</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Crecimiento</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">+{mockMetrics.users.growth}%</div>
                    <p className="text-sm text-muted-foreground">Vs. mes anterior</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="analyses" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Total Análisis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{mockMetrics.analyses.total.toLocaleString()}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Completados</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">
                      {mockMetrics.analyses.completed.toLocaleString()}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>En Proceso</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-blue-600">{mockMetrics.analyses.inProgress}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Fallidos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-red-600">{mockMetrics.analyses.failed}</div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="revenue" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Ingresos Mensuales</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">€{mockMetrics.revenue.monthly.toLocaleString()}</div>
                    <p className="text-sm text-green-600">+{mockMetrics.revenue.growth}% vs. mes anterior</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Ingresos Anuales</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">€{mockMetrics.revenue.yearly.toLocaleString()}</div>
                    <p className="text-sm text-muted-foreground">Proyección anual</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Tasa de Abandono</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-red-600">{mockMetrics.revenue.churn}%</div>
                    <p className="text-sm text-muted-foreground">Churn rate mensual</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="performance" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Tiempo Promedio</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{mockMetrics.performance.avgProcessingTime}m</div>
                    <p className="text-sm text-muted-foreground">Por análisis</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Tasa de Éxito</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">{mockMetrics.performance.successRate}%</div>
                    <p className="text-sm text-muted-foreground">Análisis exitosos</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Uptime del Sistema</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-green-600">{mockMetrics.performance.systemUptime}%</div>
                    <p className="text-sm text-muted-foreground">Disponibilidad</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Tasa de Error</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-yellow-600">{mockMetrics.performance.errorRate}%</div>
                    <p className="text-sm text-muted-foreground">Errores del sistema</p>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
