import { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Progress } from './components/ui/progress';
import { Alert, AlertDescription } from './components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ScrollArea } from './components/ui/scroll-area';
import { 
  Play, 
  Square, 
  Users, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Zap, 
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Trash2,
  Activity,
  Download
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [automationStatus, setAutomationStatus] = useState({
    is_running: false,
    status: 'stopped',
    total_accounts: 0,
    successful_accounts: 0,
    failed_accounts: 0,
    current_batch: 0,
    last_cooldown: null,
    errors: []
  });
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API}/automation/status`);
      setAutomationStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/automation/logs?limit=20`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const startAutomation = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/automation/start`);
      await fetchStatus();
    } catch (error) {
      console.error('Error starting automation:', error);
    }
    setLoading(false);
  };

  const stopAutomation = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/automation/stop`);
      await fetchStatus();
    } catch (error) {
      console.error('Error stopping automation:', error);
    }
    setLoading(false);
  };

  const resetStats = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/automation/reset`);
      await fetchStatus();
    } catch (error) {
      console.error('Error resetting stats:', error);
    }
    setLoading(false);
  };

  const clearLogs = async () => {
    setLoading(true);
    try {
      await axios.delete(`${API}/automation/logs`);
      await fetchLogs();
    } catch (error) {
      console.error('Error clearing logs:', error);
    }
    setLoading(false);
  };

  const downloadSourceCode = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/download/source`, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'steep-automation-source.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading source code:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStatus();
    fetchLogs();

    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'bg-emerald-500';
      case 'cooldown': return 'bg-amber-500';
      case 'error': return 'bg-rose-500';
      default: return 'bg-slate-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Activity className="h-4 w-4" />;
      case 'cooldown': return <Clock className="h-4 w-4" />;
      case 'error': return <AlertTriangle className="h-4 w-4" />;
      default: return <Square className="h-4 w-4" />;
    }
  };

  const successRate = automationStatus.total_accounts > 0 
    ? Math.round((automationStatus.successful_accounts / automationStatus.total_accounts) * 100)
    : 0;

  const batchProgress = (automationStatus.current_batch / 15) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Steep.gg Automation
            </h1>
          </div>
          <div className="flex items-center justify-center space-x-4">
            <p className="text-slate-400 text-lg">
              Automated waitlist signup with email verification • Referral Code: Cook
            </p>
            <Button 
              onClick={downloadSourceCode} 
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Source
            </Button>
          </div>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">Status</CardTitle>
              <div className={`w-3 h-3 rounded-full ${getStatusColor(automationStatus.status)}`}></div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(automationStatus.status)}
                <span className="text-2xl font-bold text-white capitalize">
                  {automationStatus.status}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">Total Created</CardTitle>
              <Users className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{automationStatus.total_accounts}</div>
              <p className="text-xs text-slate-400">accounts registered</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400">{successRate}%</div>
              <p className="text-xs text-slate-400">
                {automationStatus.successful_accounts} verified / {automationStatus.failed_accounts} failed
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">Batch Progress</CardTitle>
              <RefreshCw className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{automationStatus.current_batch}/15</div>
              <Progress value={batchProgress} className="mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Controls */}
        <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white">Automation Controls</CardTitle>
            <CardDescription className="text-slate-400">
              Manage the automation process and monitor performance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3">
              {!automationStatus.is_running ? (
                <Button 
                  onClick={startAutomation} 
                  disabled={loading}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <Play className="mr-2 h-4 w-4" />
                  Start Automation
                </Button>
              ) : (
                <Button 
                  onClick={stopAutomation} 
                  disabled={loading}
                  variant="destructive"
                >
                  <Square className="mr-2 h-4 w-4" />
                  Stop Automation
                </Button>
              )}
              
              <Button 
                onClick={resetStats} 
                disabled={loading}
                variant="outline"
                className="border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Reset Stats
              </Button>
              
              <Button 
                onClick={clearLogs} 
                disabled={loading}
                variant="outline"
                className="border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Clear Logs
              </Button>
            </div>

            {automationStatus.status === 'cooldown' && (
              <Alert className="bg-amber-900/20 border-amber-600">
                <Clock className="h-4 w-4" />
                <AlertDescription className="text-amber-200">
                  Rate limit cooldown active. Automation will resume automatically after 15 minutes.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Tabs for Logs and Errors */}
        <Tabs defaultValue="logs" className="space-y-4">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="logs" className="data-[state=active]:bg-slate-700">
              Account Logs
            </TabsTrigger>
            <TabsTrigger value="errors" className="data-[state=active]:bg-slate-700">
              Errors ({automationStatus.errors.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="logs">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Recent Account Creation Logs</CardTitle>
                <CardDescription className="text-slate-400">
                  Latest account registrations and verification attempts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {logs.length === 0 ? (
                      <p className="text-slate-400 text-center py-8">No logs available yet</p>
                    ) : (
                      logs.map((log, index) => (
                        <div 
                          key={index} 
                          className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-white">{log.username}</span>
                              <span className="text-sm text-slate-400">{log.email}</span>
                            </div>
                            <div className="text-xs text-slate-500">
                              Created: {new Date(log.created_at).toLocaleString()}
                              {log.verified_at && (
                                <span className="ml-4">
                                  Verified: {new Date(log.verified_at).toLocaleString()}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            {log.status === 'email_verified' ? (
                              <Badge className="bg-emerald-600 text-white">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Verified
                              </Badge>
                            ) : log.status === 'failed' ? (
                              <Badge variant="destructive">
                                <XCircle className="mr-1 h-3 w-3" />
                                Failed
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <Clock className="mr-1 h-3 w-3" />
                                Pending
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="errors">
            <Card className="bg-slate-800/50 border-slate-700 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Error Logs</CardTitle>
                <CardDescription className="text-slate-400">
                  Recent errors and issues encountered during automation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {automationStatus.errors.length === 0 ? (
                      <p className="text-slate-400 text-center py-8">No errors recorded</p>
                    ) : (
                      automationStatus.errors.map((error, index) => (
                        <Alert key={index} className="bg-rose-900/20 border-rose-600">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription className="text-rose-200">
                            {error}
                          </AlertDescription>
                        </Alert>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;