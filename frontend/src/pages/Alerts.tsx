import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Alert as MuiAlert,
  Pagination,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Info,
  Error as ErrorIcon,
  Visibility,
  Check,
  Close,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = 'http://localhost:8000/api/v1';

interface Alert {
  alert_id: string;
  battery_id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  triggered_at: string;
  resolved_at: string | null;
  is_acknowledged: boolean;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  acknowledgment_note: string | null;
  is_active: boolean;
  is_pending: boolean;
}

interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  critical_alerts: number;
  warning_alerts: number;
  info_alerts: number;
  acknowledged_alerts: number;
}

const AlertsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(20);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [acknowledgeDialogOpen, setAcknowledgeDialogOpen] = useState(false);
  const [acknowledgeNote, setAcknowledgeNote] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch alerts
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['alerts', page, severityFilter, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        skip: String((page - 1) * rowsPerPage),
        limit: String(rowsPerPage),
        active_only: statusFilter === 'active' ? 'true' : 'false',
      });

      if (severityFilter) {
        params.append('severity', severityFilter);
      }

      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/alerts?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch alert stats
  const { data: statsData } = useQuery({
    queryKey: ['alert-stats'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/alerts/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    refetchInterval: 30000,
  });

  // Acknowledge mutation
  const acknowledgeMutation = useMutation({
    mutationFn: async ({ alertId, note }: { alertId: string; note: string }) => {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_URL}/alerts/${alertId}/acknowledge`,
        { note },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
      setAcknowledgeDialogOpen(false);
      setAcknowledgeNote('');
      setSelectedAlert(null);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to acknowledge alert');
    },
  });

  // Resolve mutation
  const resolveMutation = useMutation({
    mutationFn: async (alertId: string) => {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_URL}/alerts/${alertId}/resolve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to resolve alert');
    },
  });

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'info':
        return <Info color="info" />;
      default:
        return <Info />;
    }
  };

  const getSeverityColor = (severity: string): "error" | "warning" | "info" | "default" => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  const handleAcknowledge = (alert: Alert) => {
    setSelectedAlert(alert);
    setAcknowledgeDialogOpen(true);
  };

  const handleAcknowledgeSubmit = () => {
    if (selectedAlert) {
      acknowledgeMutation.mutate({
        alertId: selectedAlert.alert_id,
        note: acknowledgeNote,
      });
    }
  };

  const handleResolve = (alertId: string) => {
    if (confirm('Are you sure you want to resolve this alert?')) {
      resolveMutation.mutate(alertId);
    }
  };

  const stats: AlertStats | undefined = statsData;
  const alerts: Alert[] = alertsData?.alerts || [];
  const totalPages = Math.ceil((alertsData?.total || 0) / rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Alerts Management
      </Typography>

      {error && (
        <MuiAlert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </MuiAlert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Total Alerts
                </Typography>
                <Typography variant="h4">{stats.total_alerts}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Active
                </Typography>
                <Typography variant="h4" color="primary">
                  {stats.active_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: '#ffebee' }}>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Critical
                </Typography>
                <Typography variant="h4" color="error">
                  {stats.critical_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: '#fff3e0' }}>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Warning
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {stats.warning_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card sx={{ bgcolor: '#e3f2fd' }}>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Info
                </Typography>
                <Typography variant="h4" color="info.main">
                  {stats.info_alerts}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="textSecondary">
                  Acknowledged
                </Typography>
                <Typography variant="h4">{stats.acknowledged_alerts}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  label="Severity"
                  onChange={(e) => {
                    setSeverityFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="warning">Warning</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setPage(1);
                  }}
                >
                  <MenuItem value="active">Active Only</MenuItem>
                  <MenuItem value="all">All Alerts</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>Battery ID</TableCell>
                <TableCell>Triggered</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : alerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No alerts found
                  </TableCell>
                </TableRow>
              ) : (
                alerts.map((alert) => (
                  <TableRow key={alert.alert_id}>
                    <TableCell>
                      <Chip
                        icon={getSeverityIcon(alert.severity)}
                        label={alert.severity.toUpperCase()}
                        color={getSeverityColor(alert.severity)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{alert.alert_type}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{alert.message}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {alert.battery_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {format(new Date(alert.triggered_at), 'MMM dd, HH:mm')}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        {alert.is_active ? (
                          <Chip label="Active" color="error" size="small" />
                        ) : (
                          <Chip label="Resolved" color="success" size="small" />
                        )}
                        {alert.is_acknowledged && (
                          <Chip
                            icon={<CheckCircle />}
                            label="Ack"
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        {!alert.is_acknowledged && alert.is_active && (
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleAcknowledge(alert)}
                            title="Acknowledge"
                          >
                            <Check />
                          </IconButton>
                        )}
                        {alert.is_active && (
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleResolve(alert.alert_id)}
                            title="Resolve"
                          >
                            <Close />
                          </IconButton>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, newPage) => setPage(newPage)}
              color="primary"
            />
          </Box>
        )}
      </Card>

      {/* Acknowledge Dialog */}
      <Dialog open={acknowledgeDialogOpen} onClose={() => setAcknowledgeDialogOpen(false)}>
        <DialogTitle>Acknowledge Alert</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Note (optional)"
            value={acknowledgeNote}
            onChange={(e) => setAcknowledgeNote(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAcknowledgeDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleAcknowledgeSubmit}
            disabled={acknowledgeMutation.isPending}
          >
            Acknowledge
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlertsPage;
