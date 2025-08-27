import React, { useState, useEffect } from "react";
import "./AssignmentManager.css";

const AssignmentManager = ({ groupId, userRole, onAssignmentCreated }) => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAssignment, setNewAssignment] = useState({
    title: "",
    description: "",
    assignment_type: "practice_session",
    due_date: "",
    skill_areas: [],
    difficulty_level: "beginner",
    min_score_required: 0.7,
    max_attempts: null,
    is_required: true,
    auto_grade: true,
    instructions: "",
  });

  const isEducator = ["owner", "educator", "moderator"].includes(userRole);

  useEffect(() => {
    loadAssignments();
  }, [groupId]);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/groups/${groupId}/assignments`);
      if (response.ok) {
        const data = await response.json();
        setAssignments(data);
      }
    } catch (error) {
      console.error("Failed to load assignments:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAssignment = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/v1/groups/${groupId}/assignments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newAssignment),
      });

      if (response.ok) {
        const assignment = await response.json();
        setAssignments([assignment, ...assignments]);
        setShowCreateForm(false);
        setNewAssignment({
          title: "",
          description: "",
          assignment_type: "practice_session",
          due_date: "",
          skill_areas: [],
          difficulty_level: "beginner",
          min_score_required: 0.7,
          max_attempts: null,
          is_required: true,
          auto_grade: true,
          instructions: "",
        });
        if (onAssignmentCreated) {
          onAssignmentCreated(assignment);
        }
      }
    } catch (error) {
      console.error("Failed to create assignment:", error);
    }
  };

  const handlePublishAssignment = async (assignmentId) => {
    try {
      const response = await fetch(
        `/api/v1/assignments/${assignmentId}/publish`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        loadAssignments(); // Reload to get updated status
      }
    } catch (error) {
      console.error("Failed to publish assignment:", error);
    }
  };

  const handleStartAssignment = async (assignmentId) => {
    try {
      const response = await fetch(
        `/api/v1/assignments/${assignmentId}/start`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        const result = await response.json();
        // Navigate to assignment or update UI
        console.log("Assignment started:", result);
      }
    } catch (error) {
      console.error("Failed to start assignment:", error);
    }
  };

  const getStatusBadge = (assignment) => {
    const { status, is_available, is_overdue } = assignment;

    if (status === "draft") {
      return <span className="badge badge-secondary">Draft</span>;
    }
    if (is_overdue) {
      return <span className="badge badge-danger">Overdue</span>;
    }
    if (!is_available) {
      return <span className="badge badge-warning">Not Available</span>;
    }
    if (status === "published") {
      return <span className="badge badge-success">Available</span>;
    }
    return <span className="badge badge-info">{status}</span>;
  };

  const getProgressBar = (assignment) => {
    const { completion_rate } = assignment;
    return (
      <div className="progress">
        <div
          className="progress-bar"
          role="progressbar"
          style={{ width: `${completion_rate}%` }}
          aria-valuenow={completion_rate}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          {completion_rate.toFixed(0)}%
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Loading assignments...</div>;
  }

  return (
    <div className="assignment-manager">
      <div className="assignment-header">
        <h3>Assignments</h3>
        {isEducator && (
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
          >
            Create Assignment
          </button>
        )}
      </div>

      {showCreateForm && (
        <div className="create-assignment-form">
          <div className="form-overlay">
            <div className="form-modal">
              <h4>Create New Assignment</h4>
              <form onSubmit={handleCreateAssignment}>
                <div className="form-group">
                  <label>Title *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={newAssignment.title}
                    onChange={(e) =>
                      setNewAssignment({
                        ...newAssignment,
                        title: e.target.value,
                      })
                    }
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    value={newAssignment.description}
                    onChange={(e) =>
                      setNewAssignment({
                        ...newAssignment,
                        description: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="form-row">
                  <div className="form-group col-md-6">
                    <label>Assignment Type</label>
                    <select
                      className="form-control"
                      value={newAssignment.assignment_type}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          assignment_type: e.target.value,
                        })
                      }
                    >
                      <option value="practice_session">Practice Session</option>
                      <option value="story_completion">Story Completion</option>
                      <option value="skill_assessment">Skill Assessment</option>
                      <option value="collaborative_session">
                        Collaborative Session
                      </option>
                    </select>
                  </div>

                  <div className="form-group col-md-6">
                    <label>Difficulty Level</label>
                    <select
                      className="form-control"
                      value={newAssignment.difficulty_level}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          difficulty_level: e.target.value,
                        })
                      }
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group col-md-6">
                    <label>Due Date</label>
                    <input
                      type="datetime-local"
                      className="form-control"
                      value={newAssignment.due_date}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          due_date: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="form-group col-md-6">
                    <label>Minimum Score Required</label>
                    <input
                      type="number"
                      className="form-control"
                      min="0"
                      max="1"
                      step="0.1"
                      value={newAssignment.min_score_required}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          min_score_required: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Instructions</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={newAssignment.instructions}
                    onChange={(e) =>
                      setNewAssignment({
                        ...newAssignment,
                        instructions: e.target.value,
                      })
                    }
                    placeholder="Detailed instructions for completing this assignment..."
                  />
                </div>

                <div className="form-check-group">
                  <div className="form-check">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="is_required"
                      checked={newAssignment.is_required}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          is_required: e.target.checked,
                        })
                      }
                    />
                    <label className="form-check-label" htmlFor="is_required">
                      Required Assignment
                    </label>
                  </div>

                  <div className="form-check">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="auto_grade"
                      checked={newAssignment.auto_grade}
                      onChange={(e) =>
                        setNewAssignment({
                          ...newAssignment,
                          auto_grade: e.target.checked,
                        })
                      }
                    />
                    <label className="form-check-label" htmlFor="auto_grade">
                      Auto-grade based on performance
                    </label>
                  </div>
                </div>

                <div className="form-actions">
                  <button type="submit" className="btn btn-primary">
                    Create Assignment
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowCreateForm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      <div className="assignments-list">
        {assignments.length === 0 ? (
          <div className="no-assignments">
            <p>No assignments found.</p>
            {isEducator && <p>Create your first assignment to get started!</p>}
          </div>
        ) : (
          assignments.map((assignment) => (
            <div key={assignment.assignment_id} className="assignment-card">
              <div className="assignment-header">
                <h5>{assignment.title}</h5>
                {getStatusBadge(assignment)}
              </div>

              {assignment.description && (
                <p className="assignment-description">
                  {assignment.description}
                </p>
              )}

              <div className="assignment-details">
                <div className="detail-item">
                  <strong>Type:</strong>{" "}
                  {assignment.assignment_type.replace("_", " ")}
                </div>
                {assignment.difficulty_level && (
                  <div className="detail-item">
                    <strong>Difficulty:</strong> {assignment.difficulty_level}
                  </div>
                )}
                {assignment.due_date && (
                  <div className="detail-item">
                    <strong>Due:</strong>{" "}
                    {new Date(assignment.due_date).toLocaleString()}
                  </div>
                )}
                {assignment.min_score_required && (
                  <div className="detail-item">
                    <strong>Min Score:</strong>{" "}
                    {(assignment.min_score_required * 100).toFixed(0)}%
                  </div>
                )}
              </div>

              {isEducator && (
                <div className="assignment-stats">
                  <div className="stat-item">
                    <strong>Submissions:</strong>{" "}
                    {assignment.completed_submissions}/
                    {assignment.total_submissions}
                  </div>
                  <div className="progress-container">
                    <label>Completion Rate:</label>
                    {getProgressBar(assignment)}
                  </div>
                  {assignment.average_score && (
                    <div className="stat-item">
                      <strong>Average Score:</strong>{" "}
                      {(assignment.average_score * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              )}

              <div className="assignment-actions">
                {isEducator ? (
                  <>
                    {assignment.status === "draft" && (
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() =>
                          handlePublishAssignment(assignment.assignment_id)
                        }
                      >
                        Publish
                      </button>
                    )}
                    <button className="btn btn-info btn-sm">
                      View Submissions
                    </button>
                    <button className="btn btn-secondary btn-sm">Edit</button>
                  </>
                ) : (
                  <>
                    {assignment.is_available &&
                      !assignment.user_submission?.is_completed && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() =>
                            handleStartAssignment(assignment.assignment_id)
                          }
                        >
                          {assignment.user_submission?.status === "in_progress"
                            ? "Continue"
                            : "Start"}
                        </button>
                      )}
                    {assignment.user_submission && (
                      <div className="submission-status">
                        <span
                          className={`status-badge status-${assignment.user_submission.status}`}
                        >
                          {assignment.user_submission.status.replace("_", " ")}
                        </span>
                        {assignment.user_submission.final_score && (
                          <span className="score">
                            Score:{" "}
                            {(
                              assignment.user_submission.final_score * 100
                            ).toFixed(1)}
                            %
                          </span>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AssignmentManager;
