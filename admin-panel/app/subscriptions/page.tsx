"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Search, CreditCard, TrendingUp, Users, DollarSign, Calendar, Download, Eye, AlertCircle } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const mockSubscriptions = [
  {
    id: "SUB-001",
    user: "Juan Pérez",
    email: "juan.perez@email.com",
    plan: "Premium",
    status: "Activa",
    startDate: "2024-01-01",
    nextPayment: "2024-02-01",
    amount: 29.99,
    paymentMethod: "Tarjeta ****1234",
    analysisCount: 45,
    analysisLimit: 100,
  },
  {
    id: "SUB-002",
    user: "María García",
    email: "maria.garcia@email.com",
    plan: "Pro",
    status: "Activa",
    startDate: "2023-12-15",
    nextPayment: "2024-01-15",
    amount: 49.99,
    paymentMethod: "PayPal",
    analysisCount: 78,
    analysisLimit: 200,
  },
  {
    id: "SUB-003",
    user: "Carlos López",
    email: "carlos.lopez@email.com",
    plan: "Premium",
    status: "Vencida",
    startDate: "2023-11-01",
    nextPayment: "2024-01-01",
    amount: 29.99,
    paymentMethod: "Tarjeta ****5678",
    analysisCount: 95,
    analysisLimit: 100,
  },
  {
    id: "SUB-004",
    user: "Ana Martínez",
    email: "ana.martinez@email.com",
    plan: "Basic",
    status: "Cancelada",
    startDate: "2023-10-01",
    nextPayment: "-",
    amount: 9.99,
    paymentMethod: "Tarjeta ****9012",
    analysisCount: 15,
    analysisLimit: 25,
  },
]

const mockPayments = [
  {
    id: "PAY-001",
    user: "Juan Pérez",
    amount: 29.99,
    plan: "Premium",
    date: "2024-01-01",
    status: "Completado",
    method: "Tarjeta",
    transactionId: "txn_1234567890",
  },
  {
    id: "PAY-002",
    user: "María García",
    amount: 49.99,
    plan: "Pro",
    date: "2023-12-15",
    status: "Completado",
    method: "PayPal",
    transactionId: "txn_0987654321",
  },
  {
    id: "PAY-003",
    user: "Carlos López",
    amount: 29.99,
    plan: "Premium",
    date: "2023-12-01",
    status: "Fallido",
    method: "Tarjeta",
    transactionId: "txn_1122334455",
  },
  {
    id: "PAY-004",
    user: "Ana Martínez",
    amount: 9.99,
    plan: "Basic",
    date: "2023-11-01",
    status: "Reembolsado",
    method: "Tarjeta",
    transactionId: "txn_5566778899",
  },
]

const upcomingPayments = [
  {
    user: "Juan Pérez",
    plan: "Premium",
    amount: 29.99,
    dueDate: "2024-02-01",
    daysUntilDue: 12,
    status: "Pendiente",
  },
  {
    user: "María García",
    plan: "Pro",
    amount: 49.99,
    dueDate: "2024-01-15",
    daysUntilDue: -5,
    status: "Vencido",
  },
  {
    user: "Luis Rodríguez",
    plan: "Premium",
    amount: 29.99,
    dueDate: "2024-01-25",
    daysUntilDue: 5,
    status: "Próximo",
  },
]

export default function SubscriptionsPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Gestión de Suscripciones</h1>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                Exportar Reporte
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Métricas de suscripciones */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Suscripciones Activas</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1,247</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-600">+12%</span> vs. mes anterior
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Ingresos Mensuales</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">€42,350</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-600">+8%</span> vs. mes anterior
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tasa de Retención</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">94.2%</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-600">+2.1%</span> vs. mes anterior
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pagos Pendientes</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">23</div>
                <p className="text-xs text-muted-foreground">€687 en total</p>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="subscriptions" className="space-y-4">
            <TabsList>
              <TabsTrigger value="subscriptions">Suscripciones</TabsTrigger>
              <TabsTrigger value="payments">Historial de Pagos</TabsTrigger>
              <TabsTrigger value="upcoming">Pagos Esperados</TabsTrigger>
            </TabsList>

            <TabsContent value="subscriptions" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Lista de Suscripciones</CardTitle>
                      <CardDescription>Gestiona todas las suscripciones de usuarios</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="relative flex-1 max-w-sm">
                      <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input placeholder="Buscar suscripciones..." className="pl-8" />
                    </div>
                    <Select>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Filtrar por plan" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos los planes</SelectItem>
                        <SelectItem value="basic">Basic</SelectItem>
                        <SelectItem value="premium">Premium</SelectItem>
                        <SelectItem value="pro">Pro</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Filtrar por estado" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos los estados</SelectItem>
                        <SelectItem value="active">Activa</SelectItem>
                        <SelectItem value="expired">Vencida</SelectItem>
                        <SelectItem value="cancelled">Cancelada</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Próximo Pago</TableHead>
                        <TableHead>Importe</TableHead>
                        <TableHead>Uso</TableHead>
                        <TableHead>Método de Pago</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockSubscriptions.map((subscription) => (
                        <TableRow key={subscription.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{subscription.user}</div>
                              <div className="text-sm text-muted-foreground">{subscription.email}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                subscription.plan === "Pro"
                                  ? "default"
                                  : subscription.plan === "Premium"
                                    ? "secondary"
                                    : "outline"
                              }
                            >
                              {subscription.plan}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                subscription.status === "Activa"
                                  ? "default"
                                  : subscription.status === "Vencida"
                                    ? "destructive"
                                    : "secondary"
                              }
                            >
                              {subscription.status}
                            </Badge>
                          </TableCell>
                          <TableCell>{subscription.nextPayment}</TableCell>
                          <TableCell>€{subscription.amount}</TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {subscription.analysisCount}/{subscription.analysisLimit}
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                              <div
                                className="bg-primary h-1.5 rounded-full"
                                style={{
                                  width: `${(subscription.analysisCount / subscription.analysisLimit) * 100}%`,
                                }}
                              ></div>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm">{subscription.paymentMethod}</TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => alert(`Ver detalles de suscripción: ${subscription.id}`)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => alert(`Gestionar pago para: ${subscription.user}`)}
                              >
                                <CreditCard className="h-4 w-4" />
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

            <TabsContent value="payments" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Historial de Pagos</CardTitle>
                  <CardDescription>Registro completo de todas las transacciones</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID Pago</TableHead>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Importe</TableHead>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Método</TableHead>
                        <TableHead>ID Transacción</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockPayments.map((payment) => (
                        <TableRow key={payment.id}>
                          <TableCell className="font-medium">{payment.id}</TableCell>
                          <TableCell>{payment.user}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{payment.plan}</Badge>
                          </TableCell>
                          <TableCell>€{payment.amount}</TableCell>
                          <TableCell>{payment.date}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                payment.status === "Completado"
                                  ? "default"
                                  : payment.status === "Fallido"
                                    ? "destructive"
                                    : "secondary"
                              }
                            >
                              {payment.status}
                            </Badge>
                          </TableCell>
                          <TableCell>{payment.method}</TableCell>
                          <TableCell className="font-mono text-xs">{payment.transactionId}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="upcoming" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Pagos Esperados
                  </CardTitle>
                  <CardDescription>Próximos pagos y renovaciones programadas</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Importe</TableHead>
                        <TableHead>Fecha de Vencimiento</TableHead>
                        <TableHead>Días Restantes</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {upcomingPayments.map((payment, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{payment.user}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{payment.plan}</Badge>
                          </TableCell>
                          <TableCell>€{payment.amount}</TableCell>
                          <TableCell>{payment.dueDate}</TableCell>
                          <TableCell>
                            <span
                              className={
                                payment.daysUntilDue < 0
                                  ? "text-red-600 font-semibold"
                                  : payment.daysUntilDue <= 7
                                    ? "text-yellow-600 font-semibold"
                                    : "text-green-600"
                              }
                            >
                              {payment.daysUntilDue < 0
                                ? `${Math.abs(payment.daysUntilDue)} días vencido`
                                : `${payment.daysUntilDue} días`}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                payment.status === "Vencido"
                                  ? "destructive"
                                  : payment.status === "Próximo"
                                    ? "secondary"
                                    : "outline"
                              }
                            >
                              {payment.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => alert(`Procesar pago para: ${payment.user}`)}
                              >
                                <CreditCard className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => alert(`Ver detalles de pago: ${payment.user}`)}
                              >
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
          </Tabs>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
