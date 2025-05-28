"use client"

import type * as React from "react"
import { Users, Video, Activity, BarChart3, Settings, Shield, Home, Server, FileText, CreditCard } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const navigationItems = [
  {
    title: "Panel Principal",
    items: [
      {
        title: "Dashboard",
        url: "/",
        icon: Home,
      },
    ],
  },
  {
    title: "Gestión",
    items: [
      {
        title: "Usuarios",
        url: "/users",
        icon: Users,
      },
      {
        title: "Análisis de Video",
        url: "/pipelines",
        icon: Video,
      },
      {
        title: "Pipeline Funnel",
        url: "/pipelines/funnel",
        icon: Activity,
      },
    ],
  },
  {
    title: "Facturación",
    items: [
      {
        title: "Suscripciones",
        url: "/subscriptions",
        icon: CreditCard,
      },
    ],
  },
  {
    title: "Monitoreo",
    items: [
      {
        title: "Microservicios",
        url: "/services",
        icon: Server,
      },
      {
        title: "Métricas",
        url: "/metrics",
        icon: BarChart3,
      },
      {
        title: "Logs",
        url: "/logs",
        icon: FileText,
      },
    ],
  },
  {
    title: "Configuración",
    items: [
      {
        title: "Sistema",
        url: "/config",
        icon: Settings,
      },
      {
        title: "Seguridad",
        url: "/security",
        icon: Shield,
      },
    ],
  },
]

export function AdminSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-4 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">Padelyzer</span>
            <span className="truncate text-xs text-muted-foreground">Admin Panel</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {navigationItems.map((group) => (
          <SidebarGroup key={group.title}>
            <SidebarGroupLabel>{group.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <a href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
