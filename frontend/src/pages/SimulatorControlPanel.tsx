import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  TextField,
  Alert,
  Stack,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Science,
  BatteryChargingFull,
  Warning,
} from '@mui/icons-material';
import axios from 'axios';

const SIMULATOR_API = 'http://localhost:8003/api/v1';

interface Battery {
  battery_id: string;
  profile: 'healthy' | 'accelerated' | 'failing';
  initial_soh: number;
}

interface SimulationStatus {
  is_running: boolean;
  batteries_count: number;
  interval_seconds: number;
  scenario: string | null;
  started_at: string | null;
  readings_generated: number;
}

interface Scenario {
  scenario: string;
  name: string;
  description: string;
  typical_conditions: Record<string, string>;
}

const SimulatorControlPanel: React.FC = () => {
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [batteries, setBatteries] = useState<Battery[]>([
    { battery_id: 'BKK_DC1_SYS01_STR01_BAT001', profile: 'healthy', initial_soh: 95.0 },
    { battery_id: 'BKK_DC1_SYS01_STR01_BAT002', profile: 'accelerated', initial_soh: 85.0 },
    { battery_id: 'BKK_DC1_SYS01_STR01_BAT003', profile: 'healthy', initial_soh: 92.0 },
  ]);
  const [intervalSeconds, setIntervalSeconds] = useState<number>(5);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
    fetchScenarios();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${SIMULATOR_API}/simulation/status`);
      setStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  const fetchScenarios = async () => {
    try {
      const response = await axios.get(`${SIMULATOR_API}/scenarios`);
      setScenarios(response.data);
    } catch (err) {
      console.error('Failed to fetch scenarios:', err);
    }
  };

  const startSimulation = async () => {
    try {
      setError(null);
      setSuccess(null);
      await axios.post(`${SIMULATOR_API}/simulation/start`, {
        batteries,
        interval_seconds: intervalSeconds,
        scenario: selectedScenario || null,
      });
      setSuccess('Simulation started successfully');
      fetchStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start simulation');
    }
  };

  const stopSimulation = async () => {
    try {
      setError(null);
      setSuccess(null);
      await axios.post(`${SIMULATOR_API}/simulation/stop`);
      setSuccess('Simulation stopped successfully');
      fetchStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop simulation');
    }
  };

  const applyScenario = async (scenarioName: string) => {
    try {
      setError(null);
      setSuccess(null);
      await axios.post(`${SIMULATOR_API}/scenarios/apply`, {
        scenario: scenarioName,
        battery_ids: null, // Apply to all
      });
      setSuccess(`Scenario "${scenarioName}" applied to all batteries`);
      fetchStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply scenario');
    }
  };

  const clearScenarios = async () => {
    try {
      setError(null);
      setSuccess(null);
      await axios.post(`${SIMULATOR_API}/scenarios/clear`, {});
      setSuccess('Scenarios cleared');
      fetchStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to clear scenarios');
    }
  };

  const addBattery = () => {
    const newId = `BKK_DC1_SYS01_STR01_BAT${String(batteries.length + 1).padStart(3, '0')}`;
    setBatteries([...batteries, { battery_id: newId, profile: 'healthy', initial_soh: 95.0 }]);
  };

  const removeBattery = (index: number) => {
    setBatteries(batteries.filter((_, i) => i !== index));
  };

  const updateBattery = (index: number, field: keyof Battery, value: any) => {
    const updated = [...batteries];
    updated[index] = { ...updated[index], [field]: value };
    setBatteries(updated);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Science /> Sensor Simulator Control Panel
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Simulation Status
          </Typography>
          {status && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">Status</Typography>
                <Chip
                  label={status.is_running ? 'Running' : 'Stopped'}
                  color={status.is_running ? 'success' : 'default'}
                  icon={status.is_running ? <PlayArrow /> : <Stop />}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">Batteries</Typography>
                <Typography variant="h6">{status.batteries_count}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">Interval</Typography>
                <Typography variant="h6">{status.interval_seconds}s</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="textSecondary">Readings Generated</Typography>
                <Typography variant="h6">{status.readings_generated.toLocaleString()}</Typography>
              </Grid>
              {status.scenario && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">Active Scenario</Typography>
                  <Chip label={status.scenario} color="primary" />
                </Grid>
              )}
            </Grid>
          )}
        </CardContent>
      </Card>

      {/* Configuration Card */}
      {!status?.is_running && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Simulation Configuration
            </Typography>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Interval (seconds)"
                  value={intervalSeconds}
                  onChange={(e) => setIntervalSeconds(Number(e.target.value))}
                  InputProps={{ inputProps: { min: 1, max: 60 } }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Initial Scenario (Optional)</InputLabel>
                  <Select
                    value={selectedScenario}
                    label="Initial Scenario (Optional)"
                    onChange={(e) => setSelectedScenario(e.target.value)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {scenarios.map((s) => (
                      <MenuItem key={s.scenario} value={s.scenario}>
                        {s.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BatteryChargingFull /> Batteries
            </Typography>

            <Stack spacing={2}>
              {batteries.map((battery, index) => (
                <Grid container spacing={2} key={index}>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Battery ID"
                      value={battery.battery_id}
                      onChange={(e) => updateBattery(index, 'battery_id', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Profile</InputLabel>
                      <Select
                        value={battery.profile}
                        label="Profile"
                        onChange={(e) => updateBattery(index, 'profile', e.target.value)}
                      >
                        <MenuItem value="healthy">Healthy</MenuItem>
                        <MenuItem value="accelerated">Accelerated</MenuItem>
                        <MenuItem value="failing">Failing</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      label="Initial SOH (%)"
                      value={battery.initial_soh}
                      onChange={(e) => updateBattery(index, 'initial_soh', Number(e.target.value))}
                      InputProps={{ inputProps: { min: 0, max: 100, step: 0.1 } }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <Button
                      fullWidth
                      variant="outlined"
                      color="error"
                      onClick={() => removeBattery(index)}
                      disabled={batteries.length === 1}
                    >
                      Remove
                    </Button>
                  </Grid>
                </Grid>
              ))}
            </Stack>

            <Button
              variant="outlined"
              onClick={addBattery}
              sx={{ mt: 2 }}
            >
              Add Battery
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Control Buttons */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Controls
          </Typography>
          <Stack direction="row" spacing={2}>
            {!status?.is_running ? (
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
                onClick={startSimulation}
                disabled={batteries.length === 0}
              >
                Start Simulation
              </Button>
            ) : (
              <Button
                variant="contained"
                color="error"
                startIcon={<Stop />}
                onClick={stopSimulation}
              >
                Stop Simulation
              </Button>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Scenarios Card */}
      {status?.is_running && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Warning /> Apply Test Scenarios
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Apply scenarios to test various operational conditions
            </Typography>

            <Grid container spacing={2}>
              {scenarios.map((scenario) => (
                <Grid item xs={12} sm={6} md={4} key={scenario.scenario}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        {scenario.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        {scenario.description}
                      </Typography>
                      <Button
                        variant="contained"
                        size="small"
                        fullWidth
                        onClick={() => applyScenario(scenario.scenario)}
                      >
                        Apply
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Button
              variant="outlined"
              onClick={clearScenarios}
              sx={{ mt: 2 }}
            >
              Clear All Scenarios
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SimulatorControlPanel;
