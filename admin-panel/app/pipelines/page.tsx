"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Search, Play, Pause, Square, MoreHorizontal, Eye, Download, RefreshCw } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"
import Link from "next/link"

const mockPipelines = [
  {
    id: "PL-001",
    user: "Juan Pérez",
    status: "Completado",
    progress: 100,
    type: "Partido",
    startTime: "2024-01-20 14:30",
    endTime: "2024-01-20 14:45",
    duration: "15m",
    framesProcessed: 12500,
    totalFrames: 12500,
  },
  {
    id: "PL-002",
    user: "María García",
    status: "En Proceso",
    progress: 65,
    type: "Entrenamiento",
    startTime: "2024-01-20 15:00",
    endTime: "-",
    duration: "8m",
    framesProcessed: 8100,
    totalFrames: 12500,
  },
  {
    id: "PL-003",
    user: "Carlos López",
    status: "En Cola",
    progress: 0,
    type: "Partido",
    startTime: "-",
    endTime: "-",
    duration: "-",
    framesProcessed: 0,
    totalFrames: 15000,
  },
  {
    id: "PL-004",
    user: "Ana Martínez",
    status: "Error",
    progress: 25,
    type: "Entrenamiento",
    startTime: "2024-01-20 13:15",
    endTime: "-",
    duration: "3m",
    framesProcessed: 3125,
    totalFrames: 12500,
  },
]

export default function PipelinesPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Análisis de Video</h1>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Estadísticas de pipelines */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Análisis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2,847</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">En Proceso</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">23</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">En Cola</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">8</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Errores (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3</div>
              </CardContent>
            </Card>
          </div>

          {/* Tabla de pipelines */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pipelines de Análisis</CardTitle>
                  <CardDescription>Monitorea el estado de todos los análisis de video</CardDescription>
                </div>
                <Button variant="outline">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Actualizar
                </Button>
              </div>
              <div className="flex items-center space-x-2">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Buscar análisis..." className="pl-8" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Progreso</TableHead>
                    <TableHead>Inicio</TableHead>
                    <TableHead>Duración</TableHead>
                    <TableHead className="w-[70px]">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockPipelines.map((pipeline) => (
                    <TableRow key={pipeline.id}>
                      <TableCell className="font-medium">{pipeline.id}</TableCell>
                      <TableCell>{pipeline.user}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{pipeline.type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            pipeline.status === "Completado"
                              ? "default"
                              : pipeline.status === "En Proceso"
                                ? "secondary"
                                : pipeline.status === "Error"
                                  ? "destructive"
                                  : "outline"
                          }
                        >
                          {pipeline.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Progress value={pipeline.progress} className="h-2" />
                          <div className="text-xs text-muted-foreground">
                            {pipeline.framesProcessed.toLocaleString()} / {pipeline.totalFrames.toLocaleString()} frames
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{pipeline.startTime}</TableCell>
                      <TableCell>{pipeline.duration}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                            <DropdownMenuItem asChild>
                              <Link href={`/pipelines/${pipeline.id}`}>
                                <Eye className="mr-2 h-4 w-4" />
                                Ver Detalles
                              </Link>
                            </DropdownMenuItem>
                            {pipeline.status === "En Proceso" && (
                              <DropdownMenuItem>
                                <Pause className="mr-2 h-4 w-4" />
                                Pausar
                              </DropdownMenuItem>
                            )}
                            {pipeline.status === "En Cola" && (
                              <DropdownMenuItem>
                                <Play className="mr-2 h-4 w-4" />
                                Iniciar
                              </DropdownMenuItem>
                            )}
                            {pipeline.status === "Completado" && (
                              <DropdownMenuItem>
                                <Download className="mr-2 h-4 w-4" />
                                Descargar
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-red-600">
                              <Square className="mr-2 h-4 w-4" />
                              Cancelar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
