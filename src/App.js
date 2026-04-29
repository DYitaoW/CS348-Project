import { useEffect, useState } from 'react';
import './App.css';

// For cloud deployment, set REACT_APP_API_BASE_URL to your backend URL, e.g.
// https://your-service-xyz-uc.a.run.app
// For local development with CRA proxy, leave it unset.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || '';

const api = async (path, options = {}) => {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
};

function App() {
  const [initStatus, setInitStatus] = useState('Not started');
  const [notice, setNotice] = useState('');
  const [tables, setTables] = useState([]);
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);

  const [teamForm, setTeamForm] = useState({
    team_id: '',
    name: '',
    city: '',
    coach_name: '',
  });

  const [playerForm, setPlayerForm] = useState({
    team_id: '',
    name: '',
    position: '',
    jersey_number: 0,
    goals: 0,
    assists: 0,
  });

  const [reportFilters, setReportFilters] = useState({
    team_id: '',
    min_goals: 0,
    min_assists: 0,
  });
  const [reportRows, setReportRows] = useState([]);
  const [reportStats, setReportStats] = useState({
    count: 0,
    avg_goals: 0,
    avg_assists: 0,
  });

  const [viewMode, setViewMode] = useState('teams');

  const refreshLookups = async () => {
    const [teamsRes, playersRes] = await Promise.all([
      api('/teams'),
      api('/players'),
    ]);
    setTeams(teamsRes);
    setPlayers(playersRes);
  };

  const handleInitDb = async () => {
    try {
      setInitStatus('Initializing...');
      if (isInitialized) {
        await api('/reset-db', { method: 'POST' });
        setInitStatus('Tables reset');
        setNotice('Database tables reset.');
      } else {
        await api('/init-db', { method: 'POST' });
        setInitStatus('Tables created');
        setNotice('Database tables created.');
      }
      setIsInitialized(true);
      await refreshLookups();
    } catch (err) {
      setInitStatus(`Error: ${err.message}`);
    }
  };

  const handleLoadTables = async () => {
    try {
      const res = await api('/tables');
      setTables(res.tables || []);
    } catch (err) {
      setTables([`Error: ${err.message}`]);
    }
  };

  const handleTeamSubmit = async (e) => {
    e.preventDefault();
    try {
      await api('/teams', {
        method: 'POST',
        body: JSON.stringify({
          name: teamForm.name,
          city: teamForm.city,
          coach_name: teamForm.coach_name,
        }),
      });
      setTeamForm({ team_id: '', name: '', city: '', coach_name: '' });
      setNotice('Team created.');
      await refreshLookups();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleTeamUpdate = async (e) => {
    e.preventDefault();
    if (!teamForm.team_id) return;
    try {
      await api(`/teams/${teamForm.team_id}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: teamForm.name,
          city: teamForm.city,
          coach_name: teamForm.coach_name,
        }),
      });
      setNotice('Team updated.');
      await refreshLookups();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleTeamDelete = async () => {
    if (!teamForm.team_id) return;
    try {
      await api(`/teams/${teamForm.team_id}`, { method: 'DELETE' });
      setTeamForm({ team_id: '', name: '', city: '', coach_name: '' });
      setNotice('Team deleted.');
      await refreshLookups();
    } catch (err) {
      alert(err.message);
    }
  };

  const handlePlayerSubmit = async (e) => {
    e.preventDefault();
    try {
      await api('/players', {
        method: 'POST',
        body: JSON.stringify(playerForm),
      });
      setPlayerForm({
        team_id: '',
        name: '',
        position: '',
        jersey_number: 0,
        goals: 0,
        assists: 0,
      });
      setNotice('Player created.');
      await refreshLookups();
    } catch (err) {
      alert(err.message);
    }
  };

  const loadReport = async () => {
    const teamPart = reportFilters.team_id
      ? `&team_id=${reportFilters.team_id}`
      : '';
    const res = await api(
      `/report/players?min_goals=${reportFilters.min_goals}` +
        `&min_assists=${reportFilters.min_assists}${teamPart}`
    );
    setReportRows(res.players || []);
    setReportStats(
      res.stats || { count: 0, avg_goals: 0, avg_assists: 0 }
    );
  };

  useEffect(() => {
    refreshLookups().catch(() => null);
  }, []);

  useEffect(() => {
    if (isInitialized) {
      handleLoadTables();
    }
  }, [isInitialized]);

  return (
    <div className={`app ${!isInitialized ? 'intro' : ''}`}>
      {!isInitialized ? (
        <section className="hero hero-full">
          <div>
            <h1>Soccer League Stat Tracker</h1>
          </div>
          <div className="hero-actions">
            <button className="primary" onClick={handleInitDb}>
              Build Tables to Start
            </button>
            <div className="status">Status: {initStatus}</div>
            {notice && <div className="notice">{notice}</div>}
          </div>
        </section>
      ) : (
        <>
          <section className="hero">
            <div>
              <h1>Soccer League Stat Tracker</h1>
            </div>
            <div className="hero-actions">
              <button className="primary" onClick={handleInitDb}>
                Reset Tables
              </button>
              <div className="status">Status: {initStatus}</div>
              {notice && <div className="notice">{notice}</div>}
            </div>
          </section>

          <section className="panel">
            <h2>Available Tables</h2>
            <div className="table-list">
              {tables.map((t) => (
                <span key={t} className="chip">
                  {t}
                </span>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2>Main Table: Teams (Add / Edit / Delete)</h2>
            <form className="grid" onSubmit={handleTeamSubmit}>
              <label>
                Select Team (for edit/delete)
                <select
                  value={teamForm.team_id}
                  onChange={(e) => {
                    const teamId = e.target.value;
                    const selected = teams.find(
                      (t) => String(t.team_id) === String(teamId)
                    );
                    setTeamForm({
                      team_id: teamId,
                      name: selected ? selected.name : '',
                      city: selected ? selected.city : '',
                      coach_name: selected ? selected.coach_name : '',
                    });
                  }}
                >
                  <option value="">-- New Team --</option>
                  {teams.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Team Name
                <input
                  required
                  type="text"
                  value={teamForm.name}
                  onChange={(e) =>
                    setTeamForm((f) => ({ ...f, name: e.target.value }))
                  }
                />
              </label>
              <label>
                City
                <input
                  required
                  type="text"
                  value={teamForm.city}
                  onChange={(e) =>
                    setTeamForm((f) => ({ ...f, city: e.target.value }))
                  }
                />
              </label>
              <label>
                Coach Name
                <input
                  required
                  type="text"
                  value={teamForm.coach_name}
                  onChange={(e) =>
                    setTeamForm((f) => ({ ...f, coach_name: e.target.value }))
                  }
                />
              </label>
              <div className="actions">
                <button className="primary" type="submit">
                  Add Team
                </button>
                <button onClick={handleTeamUpdate} type="button">
                  Update Team
                </button>
                <button
                  className="danger"
                  onClick={handleTeamDelete}
                  type="button"
                >
                  Delete Team
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <h2>Players (Add)</h2>
            <p>Numeric inputs are required for jersey, goals, and assists.</p>
            <form className="grid" onSubmit={handlePlayerSubmit}>
              <label>
                Team
                <select
                  required
                  value={playerForm.team_id}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, team_id: e.target.value }))
                  }
                >
                  <option value="">Select</option>
                  {teams.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Player Name
                <input
                  required
                  type="text"
                  value={playerForm.name}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, name: e.target.value }))
                  }
                />
              </label>
              <label>
                Position
                <input
                  required
                  type="text"
                  value={playerForm.position}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, position: e.target.value }))
                  }
                />
              </label>
              <label>
                Jersey Number
                <input
                  required
                  type="number"
                  value={playerForm.jersey_number}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, jersey_number: e.target.value }))
                  }
                />
              </label>
              <label>
                Goals
                <input
                  required
                  type="number"
                  value={playerForm.goals}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, goals: e.target.value }))
                  }
                />
              </label>
              <label>
                Assists
                <input
                  required
                  type="number"
                  value={playerForm.assists}
                  onChange={(e) =>
                    setPlayerForm((f) => ({ ...f, assists: e.target.value }))
                  }
                />
              </label>
              <div className="actions">
                <button className="primary" type="submit">
                  Add Player
                </button>
              </div>
            </form>
          </section>

          <section className="panel">
            <h2>Search for Players</h2>
            <div className="filters">
              <label>
                Team
                <select
                  value={reportFilters.team_id}
                  onChange={(e) =>
                    setReportFilters((f) => ({ ...f, team_id: e.target.value }))
                  }
                >
                  <option value="">All Teams</option>
                  {teams.map((t) => (
                    <option key={t.team_id} value={t.team_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Min Goals
                <input
                  type="number"
                  value={reportFilters.min_goals}
                  onChange={(e) =>
                    setReportFilters((f) => ({ ...f, min_goals: e.target.value }))
                  }
                />
              </label>
              <label>
                Min Assists
                <input
                  type="number"
                  value={reportFilters.min_assists}
                  onChange={(e) =>
                    setReportFilters((f) => ({ ...f, min_assists: e.target.value }))
                  }
                />
              </label>
              <button onClick={loadReport}>Run Report</button>
            </div>

            <div className="table">
              <div className="row header six">
                <div>Player</div>
                <div>Team ID</div>
                <div>Position</div>
                <div>Jersey</div>
                <div>Goals</div>
                <div>Assists</div>
              </div>
              {reportRows.map((p) => (
                <div className="row six" key={p.player_id}>
                  <div>{p.name}</div>
                  <div>{p.team_id}</div>
                  <div>{p.position}</div>
                  <div>{p.jersey_number}</div>
                  <div>{p.goals}</div>
                  <div>{p.assists}</div>
                </div>
              ))}
            </div>
            <div className="report-stats">
              <div>Total Players: {reportStats.count}</div>
              <div>Average Goals: {reportStats.avg_goals}</div>
              <div>Average Assists: {reportStats.avg_assists}</div>
            </div>
          </section>

          <section className="panel">
            <h2>Views</h2>
            <div className="actions">
              <button onClick={() => setViewMode('teams')}>All Teams</button>
              <button onClick={() => setViewMode('players')}>All Players</button>
            </div>

            {viewMode === 'teams' && (
              <div className="table">
                <div className="row header three">
                  <div>Team</div>
                  <div>City</div>
                  <div>Coach</div>
                </div>
                {teams.map((t) => (
                  <div className="row three" key={t.team_id}>
                    <div>{t.name}</div>
                    <div>{t.city}</div>
                    <div>{t.coach_name}</div>
                  </div>
                ))}
              </div>
            )}

            {viewMode === 'players' && (
              <div className="table">
                <div className="row header six">
                  <div>Player</div>
                  <div>Team ID</div>
                  <div>Position</div>
                  <div>Jersey</div>
                  <div>Goals</div>
                  <div>Assists</div>
                </div>
                {players.map((p) => (
                  <div className="row six" key={p.player_id}>
                    <div>{p.name}</div>
                    <div>{p.team_id}</div>
                    <div>{p.position}</div>
                    <div>{p.jersey_number}</div>
                    <div>{p.goals}</div>
                    <div>{p.assists}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default App;
