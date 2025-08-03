import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Checkbox } from './components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Package, 
  RotateCcw, 
  PlusCircle,
  BarChart3,
  Calendar
} from 'lucide-react';
import './App.css';

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [clientes, setClientes] = useState([]);
  const [ventasPendientes, setVentasPendientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Estados para filtros de fecha
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFinal, setFechaFinal] = useState('');

  // Estados para formularios
  const [ventaForm, setVentaForm] = useState({
    cliente_id: '',
    producto: '',
    fecha_venta: '',
    valor_venta: '',
    ganancia: ''
  });

  const [clienteForm, setClienteForm] = useState({
    nombre: '',
    apellidos: '',
    telefono: ''
  });

  const [gastoForm, setGastoForm] = useState({
    concepto: '',
    valor: '',
    fecha_inicio: '',
    fecha_final: ''
  });

  // Estado para edición de ventas
  const [ventaEditando, setVentaEditando] = useState(null);
  const [editForm, setEditForm] = useState({
    fecha_entrega: '',
    entregado: null,
    valor_perdida: 0
  });

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      
      // Construir URL del dashboard con filtros de fecha
      let dashboardUrl = `${BACKEND_URL}/api/dashboard`;
      const params = new URLSearchParams();
      
      if (fechaInicio && fechaFinal) {
        params.append('fecha_inicio', fechaInicio);
        params.append('fecha_final', fechaFinal);
        dashboardUrl += `?${params.toString()}`;
      }
      
      const [dashboardRes, clientesRes, ventasPendientesRes] = await Promise.all([
        axios.get(dashboardUrl),
        axios.get(`${BACKEND_URL}/api/clientes`),
        axios.get(`${BACKEND_URL}/api/ventas/pendientes`)
      ]);
      
      setDashboardData(dashboardRes.data);
      setClientes(clientesRes.data);
      setVentasPendientes(ventasPendientesRes.data);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const aplicarFiltrosFecha = () => {
    if (fechaInicio && fechaFinal) {
      cargarDatos();
    } else {
      alert('Por favor selecciona ambas fechas');
    }
  };

  const limpiarFiltros = () => {
    setFechaInicio('');
    setFechaFinal('');
    // Recargar datos sin filtros
    setTimeout(() => {
      cargarDatos();
    }, 100);
  };

  const crearVenta = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${BACKEND_URL}/api/ventas`, ventaForm);
      alert('Venta creada exitosamente');
      setVentaForm({
        cliente_id: '',
        producto: '',
        fecha_venta: '',
        valor_venta: '',
        ganancia: ''
      });
      cargarDatos();
    } catch (error) {
      console.error('Error creando venta:', error);
      alert('Error al crear venta');
    }
  };

  const editarVenta = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${BACKEND_URL}/api/ventas/${ventaEditando.id}`, editForm);
      alert('Venta actualizada exitosamente');
      setVentaEditando(null);
      setEditForm({
        fecha_entrega: '',
        entregado: null,
        valor_perdida: 0
      });
      cargarDatos();
    } catch (error) {
      console.error('Error actualizando venta:', error);
      alert('Error al actualizar venta');
    }
  };

  const iniciarEdicion = (venta) => {
    setVentaEditando(venta);
    setEditForm({
      fecha_entrega: venta.fecha_entrega || '',
      entregado: venta.entregado,
      valor_perdida: venta.valor_perdida || 0
    });
  };

  const crearCliente = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${BACKEND_URL}/api/clientes`, clienteForm);
      alert('Cliente creado exitosamente');
      setClienteForm({ nombre: '', apellidos: '', telefono: '' });
      cargarDatos();
    } catch (error) {
      console.error('Error creando cliente:', error);
      alert('Error al crear cliente');
    }
  };

  const crearGasto = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${BACKEND_URL}/api/gastos`, gastoForm);
      alert('Gasto creado exitosamente');
      setGastoForm({
        concepto: '',
        valor: '',
        fecha_inicio: '',
        fecha_final: ''
      });
      cargarDatos();
    } catch (error) {
      console.error('Error creando gasto:', error);
      alert('Error al crear gasto');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando datos...</p>
        </div>
      </div>
    );
  }

  // Configuración de gráficos
  const ventasPorDiaConfig = {
    labels: dashboardData?.ventas_por_dia?.map(d => new Date(d.fecha).toLocaleDateString()) || [],
    datasets: [{
      label: 'Ventas por Día',
      data: dashboardData?.ventas_por_dia?.map(d => d.ventas) || [],
      backgroundColor: 'rgba(126, 123, 173, 0.8)',
      borderColor: 'rgba(126, 123, 173, 1)',
      borderWidth: 2,
      borderRadius: 4,
    }]
  };

  const gananciasPorProductoConfig = {
    labels: dashboardData?.ganancias_por_producto?.map(p => p.producto) || [],
    datasets: [{
      data: dashboardData?.ganancias_por_producto?.map(p => p.ganancia) || [],
      backgroundColor: [
        'rgba(135, 90, 123, 0.8)',
        'rgba(126, 123, 173, 0.8)',
        'rgba(16, 185, 129, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(156, 163, 175, 0.8)'
      ],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  };

  const resumenFinancieroConfig = {
    labels: ['Ganancias', 'Pérdidas', 'Inversión Publicidad'],
    datasets: [{
      data: [
        dashboardData?.ganancias_totales || 0,
        dashboardData?.perdidas_totales || 0,
        dashboardData?.inversion_publicidad || 0
      ],
      backgroundColor: [
        'rgba(16, 185, 129, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(59, 130, 246, 0.8)'
      ],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            family: 'system-ui',
            size: 12
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-8 w-8 text-purple-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                Control de Gastos y Ganancias
              </h1>
            </div>
            <Badge variant="secondary" className="text-sm">
              Sistema de Gestión v1.0
            </Badge>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full max-w-md">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="ventas">Ventas</TabsTrigger>
            <TabsTrigger value="clientes">Clientes</TabsTrigger>
            <TabsTrigger value="gastos">Gastos</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Filtros de fecha */}
            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-purple-600" />
                  Filtros de Fecha
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                  <div className="space-y-2">
                    <Label htmlFor="fecha_inicio">Fecha Inicial</Label>
                    <Input
                      type="date"
                      value={fechaInicio}
                      onChange={(e) => setFechaInicio(e.target.value)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="fecha_final">Fecha Final</Label>
                    <Input
                      type="date"
                      value={fechaFinal}
                      onChange={(e) => setFechaFinal(e.target.value)}
                    />
                  </div>
                  
                  <Button 
                    onClick={aplicarFiltrosFecha}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    Aplicar Filtros
                  </Button>
                  
                  <Button 
                    onClick={limpiarFiltros}
                    variant="outline"
                    className="border-gray-300"
                  >
                    Limpiar Filtros
                  </Button>
                </div>
                
                {fechaInicio && fechaFinal && (
                  <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <p className="text-sm text-purple-800">
                      Mostrando datos desde <strong>{fechaInicio}</strong> hasta <strong>{fechaFinal}</strong>
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
            {/* Métricas principales */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <Card className="bg-white shadow-sm border border-gray-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Ganancias Totales</p>
                      <p className="text-2xl font-bold text-green-600">
                        ${(dashboardData?.ganancias_totales || 0).toLocaleString()}
                      </p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-sm border border-gray-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Pérdidas</p>
                      <p className="text-2xl font-bold text-red-600">
                        ${(dashboardData?.perdidas_totales || 0).toLocaleString()}
                      </p>
                    </div>
                    <TrendingDown className="h-8 w-8 text-red-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-sm border border-gray-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Inversión Publicidad</p>
                      <p className="text-2xl font-bold text-blue-600">
                        ${(dashboardData?.inversion_publicidad || 0).toLocaleString()}
                      </p>
                    </div>
                    <DollarSign className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-sm border border-gray-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Productos Vendidos</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {dashboardData?.productos_vendidos || 0}
                      </p>
                    </div>
                    <Package className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-sm border border-gray-200">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Productos Devueltos</p>
                      <p className="text-2xl font-bold text-gray-600">
                        {dashboardData?.productos_devueltos || 0}
                      </p>
                    </div>
                    <RotateCcw className="h-8 w-8 text-gray-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Gráficos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-white shadow-sm border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-lg font-semibold text-gray-900">
                    Ventas por Día (Últimos 7 días)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div style={{ height: '300px' }}>
                    <Bar data={ventasPorDiaConfig} options={chartOptions} />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-sm border border-gray-200">
                <CardHeader>
                  <CardTitle className="text-lg font-semibold text-gray-900">
                    Ganancias por Producto
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div style={{ height: '300px' }}>
                    <Doughnut data={gananciasPorProductoConfig} options={{
                      ...chartOptions,
                      scales: undefined
                    }} />
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Resumen Financiero
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div style={{ height: '300px' }}>
                  <Doughnut data={resumenFinancieroConfig} options={{
                    ...chartOptions,
                    scales: undefined
                  }} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Ventas Tab */}
          <TabsContent value="ventas" className="space-y-6">
            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-purple-600" />
                  Registrar Nueva Venta
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={crearVenta} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="cliente">Cliente</Label>
                    <Select 
                      value={ventaForm.cliente_id} 
                      onValueChange={(value) => setVentaForm({...ventaForm, cliente_id: value})}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar cliente" />
                      </SelectTrigger>
                      <SelectContent>
                        {clientes.map((cliente) => (
                          <SelectItem key={cliente.id} value={cliente.id}>
                            {cliente.nombre} {cliente.apellidos}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="producto">Producto</Label>
                    <Input
                      type="text"
                      value={ventaForm.producto}
                      onChange={(e) => setVentaForm({...ventaForm, producto: e.target.value})}
                      placeholder="Nombre del producto"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_venta">Fecha de Venta</Label>
                    <Input
                      type="date"
                      value={ventaForm.fecha_venta}
                      onChange={(e) => setVentaForm({...ventaForm, fecha_venta: e.target.value})}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_entrega">Fecha de Entrega</Label>
                    <Input
                      type="date"
                      value={ventaForm.fecha_entrega}
                      onChange={(e) => setVentaForm({...ventaForm, fecha_entrega: e.target.value})}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="valor_venta">Valor de Venta</Label>
                    <Input
                      type="number"
                      value={ventaForm.valor_venta}
                      onChange={(e) => setVentaForm({...ventaForm, valor_venta: e.target.value})}
                      placeholder="Valor en pesos"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ganancia">Ganancia</Label>
                    <Input
                      type="number"
                      value={ventaForm.ganancia}
                      onChange={(e) => setVentaForm({...ventaForm, ganancia: e.target.value})}
                      placeholder="Ganancia esperada"
                      required
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox 
                      checked={ventaForm.entregado} 
                      onCheckedChange={(checked) => setVentaForm({...ventaForm, entregado: checked})}
                    />
                    <Label>Producto entregado</Label>
                  </div>

                  {!ventaForm.entregado && (
                    <div className="space-y-2">
                      <Label htmlFor="valor_perdida">Valor de Pérdida</Label>
                      <Input
                        type="number"
                        value={ventaForm.valor_perdida}
                        onChange={(e) => setVentaForm({...ventaForm, valor_perdida: parseFloat(e.target.value) || 0})}
                        placeholder="Pérdida por devolución"
                      />
                    </div>
                  )}

                  <div className="md:col-span-2">
                    <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700">
                      Registrar Venta
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Clientes Tab */}
          <TabsContent value="clientes" className="space-y-6">
            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-purple-600" />
                  Registrar Nuevo Cliente
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={crearCliente} className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="nombre">Nombre</Label>
                    <Input
                      type="text"
                      value={clienteForm.nombre}
                      onChange={(e) => setClienteForm({...clienteForm, nombre: e.target.value})}
                      placeholder="Nombre"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="apellidos">Apellidos</Label>
                    <Input
                      type="text"
                      value={clienteForm.apellidos}
                      onChange={(e) => setClienteForm({...clienteForm, apellidos: e.target.value})}
                      placeholder="Apellidos"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="telefono">Teléfono</Label>
                    <Input
                      type="tel"
                      value={clienteForm.telefono}
                      onChange={(e) => setClienteForm({...clienteForm, telefono: e.target.value})}
                      placeholder="Número de teléfono"
                      required
                    />
                  </div>

                  <div className="md:col-span-3">
                    <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700">
                      Registrar Cliente
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Lista de clientes */}
            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                  Clientes Registrados ({clientes.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {clientes.map((cliente) => (
                    <div key={cliente.id} className="p-4 border border-gray-200 rounded-lg">
                      <h4 className="font-semibold text-gray-900">
                        {cliente.nombre} {cliente.apellidos}
                      </h4>
                      <p className="text-sm text-gray-600">{cliente.telefono}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Gastos Tab */}
          <TabsContent value="gastos" className="space-y-6">
            <Card className="bg-white shadow-sm border border-gray-200">
              <CardHeader>
                <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-purple-600" />
                  Registrar Gasto de Publicidad
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={crearGasto} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="concepto">Concepto</Label>
                    <Input
                      type="text"
                      value={gastoForm.concepto}
                      onChange={(e) => setGastoForm({...gastoForm, concepto: e.target.value})}
                      placeholder="Ej: Facebook Ads, Google Ads"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="valor">Valor</Label>
                    <Input
                      type="number"
                      value={gastoForm.valor}
                      onChange={(e) => setGastoForm({...gastoForm, valor: e.target.value})}
                      placeholder="Valor invertido"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_inicio">Fecha de Inicio</Label>
                    <Input
                      type="date"
                      value={gastoForm.fecha_inicio}
                      onChange={(e) => setGastoForm({...gastoForm, fecha_inicio: e.target.value})}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_final">Fecha Final</Label>
                    <Input
                      type="date"
                      value={gastoForm.fecha_final}
                      onChange={(e) => setGastoForm({...gastoForm, fecha_final: e.target.value})}
                      required
                    />
                  </div>

                  <div className="md:col-span-2">
                    <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700">
                      Registrar Gasto
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;