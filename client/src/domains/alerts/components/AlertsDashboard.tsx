import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import Spinner from "../../../shared/Spinner";
import { toast } from "sonner";

const TRIGGER_LABELS: Record<string, string> = {
  new_opportunity: "NEW OPP",
  price_drop: "PX DROP",
  undervalued: "UNDERVALUED",
  auction_ending: "AUC ENDING",
};

import { alertsApi } from "../api/alerts.api";

function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: alertsApi.getAlerts,
  });
}

export default function AlertsDashboard() {
  const { data: alerts = [], isLoading, refetch } = useAlerts();
  const [showCreate, setShowCreate] = useState(false);
  const [newAlert, setNewAlert] = useState({
    name: "",
    trigger_type: "new_opportunity",
    min_profit: 10,
  });

  const displayed = alerts;

  const toggleAlertMutation = useMutation({
    mutationFn: async (id: string) => {
      const alert = displayed.find((a: any) => a.id === id);
      if (!alert) return;
      await alertsApi.updateAlert(id, { is_active: !alert.is_active });
    },
    onSuccess: () => {
      refetch();
      toast.success(`Rule "${alert.name.toUpperCase()}" status updated!`);
    },
    onError: () => {
      toast.error("Failed to update alert status");
    },
  });

  const removeAlertMutation = useMutation({
    mutationFn: async (id: string) => {
      await alertsApi.deleteAlert(id);
    },
    onSuccess: () => {
      refetch();
      toast.success("Alert successfully deleted!");
    },
    onError: () => {
      toast.error("Failed to delete alert");
    },
  });

  const createAlertMutation = useMutation({
    mutationFn: async () => {
      if (!newAlert.name.trim()) return;
      await alertsApi.createAlert({
        name: newAlert.name,
        trigger_type: newAlert.trigger_type,
        conditions: { min_profit_gbp: newAlert.min_profit },
        delivery_channel: "telegram",
      });
    },
    onSuccess: () => {
      toast.success(`Rule "${newAlert.name.toUpperCase()}" successfully deployed!`);
      setShowCreate(false);
      setNewAlert({ name: "", trigger_type: "new_opportunity", min_profit: 10 });
      refetch();
    },
    onError: () => {
      toast.error("Failed to create alert");
    },
  });

  return (
    <div className="main-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">CONDITION TRIGGERS</h1>
          <p className="view-primary-metric">Execution Rules</p>
        </div>
        <div className="control-bar" style={{ marginBottom: 0 }}>
          <button className="btn-dense btn-action" onClick={() => setShowCreate((v) => !v)}>
            {showCreate ? "CANCEL ADD" : "ADD TRIGGER RULE"}
          </button>
        </div>
      </div>

      <div className="content-pad">
        {showCreate && (
          <div
            className="panel"
            style={{ marginBottom: 24, borderLeft: "2px solid var(--text-main)" }}
          >
            <div className="view-title" style={{ marginBottom: 16 }}>
              NEW TRIGGER RULE PARAMETERS
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "auto auto auto 1fr",
                gap: 16,
                alignItems: "flex-end",
              }}
            >
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
                  RULE IDENTIFIER
                </div>
                <input
                  className="input-dense"
                  style={{ width: 200 }}
                  placeholder="E.G. CHARIZARD SWING"
                  value={newAlert.name}
                  onChange={(e) =>
                    setNewAlert((p) => ({ ...p, name: e.target.value.toUpperCase() }))
                  }
                />
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
                  EVENT CONDITION
                </div>
                <select
                  className="input-dense"
                  style={{ width: 160 }}
                  value={newAlert.trigger_type}
                  onChange={(e) => setNewAlert((p) => ({ ...p, trigger_type: e.target.value }))}
                >
                  {Object.entries(TRIGGER_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
                  THRESHOLD (GBP)
                </div>
                <input
                  className="input-dense"
                  style={{ width: 100 }}
                  type="number"
                  min={0}
                  value={newAlert.min_profit}
                  onChange={(e) =>
                    setNewAlert((p) => ({ ...p, min_profit: Number(e.target.value) }))
                  }
                />
              </div>
              <div>
                <button
                  className="btn-dense btn-action"
                  onClick={() => createAlertMutation.mutate()}
                  disabled={createAlertMutation.isPending}
                >
                  {createAlertMutation.isPending ? "DEPLOYING..." : "DEPLOY RULE"}
                </button>
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <Spinner label="LOADING TRIGGERS..." />
        ) : displayed.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [NO ACTIVE TRIGGERS CONFIGURED]
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>STATUS</th>
                <th>IDENTIFIER</th>
                <th>EVENT TYPE</th>
                <th className="right">PARAMETERS</th>
                <th>ROUTE</th>
                <th className="right">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map((a: any) => (
                <tr key={a.id} style={{ opacity: a.is_active ? 1 : 0.5 }}>
                  <td
                    className="mono"
                    style={{ color: a.is_active ? "var(--profit)" : "var(--text-muted)" }}
                  >
                    {a.is_active ? "RUNNING" : "HALTED"}
                  </td>
                  <td style={{ fontWeight: 500 }}>{a.name.toUpperCase()}</td>
                  <td className="mono">
                    {TRIGGER_LABELS[a.trigger_type] ?? a.trigger_type.toUpperCase()}
                  </td>
                  <td className="right mono">
                    {a.conditions?.min_profit_gbp != null
                      ? `MIN SPREAD >= £${a.conditions.min_profit_gbp}`
                      : "-"}
                  </td>
                  <td className="mono">TELEGRAM</td>
                  <td className="right">
                    <button
                      className="btn-dense"
                      onClick={() => toggleAlertMutation.mutate(a.id)}
                      style={{ marginRight: 8 }}
                    >
                      {toggleAlertMutation.isPending
                        ? "UPDATING..."
                        : a.is_active
                          ? "HALT"
                          : "START"}
                    </button>
                    <button
                      className="btn-dense"
                      onClick={() => removeAlertMutation.mutate(a.id)}
                      style={{ color: "var(--loss)" }}
                    >
                      {removeAlertMutation.isPending ? "DEL..." : "DEL"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
