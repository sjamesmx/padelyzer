"use client"

import { AdminSidebar } from "@/components/admin-sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Upload, Settings, Eye, Activity, BarChart3, Download, CheckCircle, Play } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

const pipelineSteps = [
  {
    id: 1,
    name: "Subida de Video",
    icon: Upload,
    count: 45,
    percentage: 100,
    color: "bg-blue-500",
    analyses: [
      { id: "PL-045", user: "Juan Pérez", status: "En proceso", time: "2m" },
      { id: "PL-044", user: "María García", status: "En proceso", time: "1m" },
    ],
  },
  {
    id: 2,
    name: "Preprocesamiento",
    icon: Settings,
    count: 38,
    percentage: 84,
    color: "bg-green-500",
    analyses: [
      { id: "PL-043", user: "Carlos López", status: "En proceso", time: "5m" },
      { id: "PL-042", user: "Ana Martínez", status: "En proceso", time: "3m" },
    ],
  },
  {
    id: 3,
    name: "Detección",
    icon: Eye,
    count: 32,
    percentage: 71,
    color: "bg-yellow-500",
    analyses: [
      { id: "PL-041", user: "Luis Rodríguez", status: "En proceso", time: "8m" },
      { id: "PL-040", user: "Carmen Silva", status: "En proceso", time: "6m" },
    ],
  },
  {
    id: 4,
    name: "Tracking",
    icon: Activity,
    count: 28,
    percentage: 62,
    color: "bg-orange-500",
    analyses: [
      { id: "PL-039", user: "Pedro Gómez", status: "En proceso", time: "12m" },
      { id: "PL-038", user: "Laura Torres", status: "Bloqueado", time: "15m" },
    ],
  },
  {
    id: 5,
    name: "Análisis Biomecánico",
    icon: BarChart3,
    count: 23,
    percentage: 51,
    color: "bg-purple-500",
    analyses: [
      { id: "PL-037", user: "Miguel Herrera", status: "En proceso", time: "18m" },
      { id: "PL-036", user: "Sofia Ruiz", status: "En proceso", time: "20m" },
    ],
  },
  {
    id: 6,
    name: "Exportación",
    icon: Download,
    count: 19,
    percentage: 42,
    color: "bg-indigo-500",
    analyses: [
      { id: "PL-035", user: "Diego Morales", status: "En proceso", time: "22m" },
      { id: "PL-034", user: "Elena Vega", status: "En proceso", time: "25m" },
    ],
  },
  {
    id: 7,
    name: "Finalización",
    icon: CheckCircle,
    count: 17,
    percentage: 38,
    color: "bg-green-600",
    analyses: [
      { id: "PL-033", user: "Roberto Castro", status: "Completado", time: "28m" },
      { id: "PL-032", user: "Patricia Jiménez", status: "Completado", time: "30m" },
    ],
  },
]

export default function PipelineFunnelPage() {
  return (
    <SidebarProvider>
      <AdminSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex flex-1 items-center justify-between">
            <h1 className="text-lg font-semibold">Pipeline de Análisis - Vista Funnel</h1>
            <ThemeToggle />
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4">
          {/* Funnel Visualization */}
          <Card>
            <CardHeader>
              <CardTitle>Embudo de Procesamiento</CardTitle>
              <CardDescription>Visualización del flujo de análisis por cada etapa del pipeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {pipelineSteps.map((step, index) => (
                  <div key={step.id} className="relative">
                    <div className="flex items-center gap-4">
                      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${step.color} text-white`}>
                        <step.icon className="h-6 w-6" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold">{step.name}</h3>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">{step.count} análisis</span>
                            <span className="text-sm font-semibold">{step.percentage}%</span>
                          </div>
                        </div>
                        <Progress value={step.percentage} className="h-3" />
                      </div>
                    </div>
                    {index < pipelineSteps.length - 1 && <div className="ml-6 mt-2 mb-2 h-4 w-0.5 bg-border"></div>}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Step Analysis */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {pipelineSteps.slice(0, 6).map((step) => (
              <Card key={step.id}>
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <step.icon className="h-4 w-4" />
                    {step.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Análisis activos:</span>
                    <span className="font-semibold">{step.count}</span>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Análisis en esta etapa:</h4>
                    {step.analyses.map((analysis) => (
                      <div key={analysis.id} className="flex items-center justify-between text-xs">
                        <div>
                          <div className="font-medium">{analysis.id}</div>
                          <div className="text-muted-foreground">{analysis.user}</div>
                        </div>
                        <div className="text-right">
                          <Badge
                            variant={analysis.status === "Bloqueado" ? "destructive" : "secondary"}
                            className="text-xs"
                          >
                            {analysis.status}
                          </Badge>
                          <div className="text-muted-foreground">{analysis.time}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-1 pt-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      Ver Todos
                    </Button>
                    {step.analyses.some((a) => a.status === "Bloqueado") && (
                      <Button size="sm" variant="destructive" className="flex-1">
                        <Play className="h-3 w-3 mr-1" />
                        Desatorar
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
