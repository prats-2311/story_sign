import React, { useState, useEffect } from "react";
import "./FriendsManager.css";

const FriendsManager = ({ userId }) => {
  const [activeTab, setActiveTab] = useState("friends");
  const [friends, setFriends] = useState([]);
  const [friendRequests, setFriendRequests] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFriendsData();
  }, []);

  const loadFriendsData = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/social/friends?include_pending=true");

      if (!response.ok) {
        throw new Error("Failed to load friends data");
      }

      const data = await response.json();
      setFriends(data.friends || []);
      setFriendRequests([
        ...(data.incoming_requests || []),
        ...(data.outgoing_requests || []),
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch(
        `/api/social/users/search?q=${encodeURIComponent(query)}`
      );

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setSearchResults(data.users || []);
    } catch (err) {
      console.error("Search error:", err);
      setSearchResults([]);
    }
  };

  const sendFriendRequest = async (username) => {
    try {
      const response = await fetch("/api/social/friends/request", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          message: `Hi! I'd like to connect and practice ASL together.`,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send friend request");
      }

      // Refresh data and clear search
      await loadFriendsData();
      setSearchQuery("");
      setSearchResults([]);

      // Show success message
      alert("Friend request sent successfully!");
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const respondToFriendRequest = async (friendshipId, accept) => {
    try {
      const response = await fetch(
        `/api/social/friends/respond/${friendshipId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ accept }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to respond to friend request");
      }

      // Refresh data
      await loadFriendsData();

      const action = accept ? "accepted" : "declined";
      alert(`Friend request ${action} successfully!`);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const removeFriend = async (friendshipId) => {
    if (!confirm("Are you sure you want to remove this friend?")) {
      return;
    }

    try {
      const response = await fetch(`/api/social/friends/${friendshipId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to remove friend");
      }

      // Refresh data
      await loadFriendsData();
      alert("Friend removed successfully");
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    // Debounce search
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      searchUsers(query);
    }, 300);
  };

  if (loading && friends.length === 0) {
    return (
      <div className="friends-manager">
        <div className="loading-spinner">Loading friends...</div>
      </div>
    );
  }

  return (
    <div className="friends-manager">
      <div className="friends-header">
        <h2>Social Connections</h2>
        <div className="tab-navigation">
          <button
            className={activeTab === "friends" ? "active" : ""}
            onClick={() => setActiveTab("friends")}
          >
            Friends ({friends.length})
          </button>
          <button
            className={activeTab === "requests" ? "active" : ""}
            onClick={() => setActiveTab("requests")}
          >
            Requests ({friendRequests.length})
          </button>
          <button
            className={activeTab === "search" ? "active" : ""}
            onClick={() => setActiveTab("search")}
          >
            Find Friends
          </button>
        </div>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      <div className="tab-content">
        {activeTab === "friends" && (
          <FriendsTab friends={friends} onRemoveFriend={removeFriend} />
        )}

        {activeTab === "requests" && (
          <RequestsTab
            requests={friendRequests}
            onRespondToRequest={respondToFriendRequest}
          />
        )}

        {activeTab === "search" && (
          <SearchTab
            searchQuery={searchQuery}
            onSearchChange={handleSearchChange}
            searchResults={searchResults}
            onSendRequest={sendFriendRequest}
          />
        )}
      </div>
    </div>
  );
};

const FriendsTab = ({ friends, onRemoveFriend }) => {
  if (friends.length === 0) {
    return (
      <div className="empty-state">
        <p>You don't have any friends yet.</p>
        <p>Use the "Find Friends" tab to connect with other learners!</p>
      </div>
    );
  }

  return (
    <div className="friends-list">
      {friends.map((friendData) => (
        <FriendCard
          key={friendData.friendship.friendship_id}
          friend={friendData.friend}
          friendship={friendData.friendship}
          onRemove={() => onRemoveFriend(friendData.friendship.friendship_id)}
        />
      ))}
    </div>
  );
};

const RequestsTab = ({ requests, onRespondToRequest }) => {
  if (requests.length === 0) {
    return (
      <div className="empty-state">
        <p>No pending friend requests.</p>
      </div>
    );
  }

  const incomingRequests = requests.filter((req) => !req.is_requester);
  const outgoingRequests = requests.filter((req) => req.is_requester);

  return (
    <div className="requests-container">
      {incomingRequests.length > 0 && (
        <div className="requests-section">
          <h3>Incoming Requests</h3>
          <div className="requests-list">
            {incomingRequests.map((request) => (
              <RequestCard
                key={request.friendship_id}
                request={request}
                type="incoming"
                onRespond={onRespondToRequest}
              />
            ))}
          </div>
        </div>
      )}

      {outgoingRequests.length > 0 && (
        <div className="requests-section">
          <h3>Sent Requests</h3>
          <div className="requests-list">
            {outgoingRequests.map((request) => (
              <RequestCard
                key={request.friendship_id}
                request={request}
                type="outgoing"
                onRespond={onRespondToRequest}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const SearchTab = ({
  searchQuery,
  onSearchChange,
  searchResults,
  onSendRequest,
}) => {
  return (
    <div className="search-container">
      <div className="search-input-container">
        <input
          type="text"
          placeholder="Search for users by username or name..."
          value={searchQuery}
          onChange={onSearchChange}
          className="search-input"
        />
      </div>

      {searchQuery && (
        <div className="search-results">
          {searchResults.length === 0 ? (
            <p className="no-results">
              No users found matching "{searchQuery}"
            </p>
          ) : (
            <div className="users-list">
              {searchResults.map((user) => (
                <UserSearchCard
                  key={user.id}
                  user={user}
                  onSendRequest={() => onSendRequest(user.username)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {!searchQuery && (
        <div className="search-help">
          <p>Search for other ASL learners to connect with!</p>
          <p>You can search by username or name.</p>
        </div>
      )}
    </div>
  );
};

const FriendCard = ({ friend, friendship, onRemove }) => {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="friend-card">
      <div className="friend-info">
        <div className="friend-avatar">
          {friend.first_name ? friend.first_name[0] : friend.username[0]}
        </div>
        <div className="friend-details">
          <h4>{friend.username}</h4>
          {friend.first_name && (
            <p>
              {friend.first_name} {friend.last_name}
            </p>
          )}
          <div className="friendship-stats">
            <span>
              Friends since{" "}
              {new Date(friendship.requested_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      <div className="friend-actions">
        <button
          className="settings-btn"
          onClick={() => setShowSettings(!showSettings)}
        >
          ⚙️
        </button>
        <button className="remove-btn" onClick={onRemove}>
          Remove
        </button>
      </div>

      {showSettings && (
        <div className="friendship-settings">
          <h5>Privacy Settings</h5>
          <label>
            <input
              type="checkbox"
              checked={friendship.settings.allow_progress_sharing}
              readOnly
            />
            Share progress updates
          </label>
          <label>
            <input
              type="checkbox"
              checked={friendship.settings.allow_session_invites}
              readOnly
            />
            Allow session invites
          </label>
          <label>
            <input
              type="checkbox"
              checked={friendship.settings.allow_feedback}
              readOnly
            />
            Allow feedback
          </label>
        </div>
      )}
    </div>
  );
};

const RequestCard = ({ request, type, onRespond }) => {
  return (
    <div className="request-card">
      <div className="request-info">
        <div className="request-avatar">
          {request.friend_id ? request.friend_id[0] : "?"}
        </div>
        <div className="request-details">
          <h4>Friend Request</h4>
          <p>
            {type === "incoming" ? "Wants to connect with you" : "Request sent"}
          </p>
          <span className="request-date">
            {new Date(request.requested_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="request-actions">
        {type === "incoming" ? (
          <>
            <button
              className="accept-btn"
              onClick={() => onRespond(request.friendship_id, true)}
            >
              Accept
            </button>
            <button
              className="decline-btn"
              onClick={() => onRespond(request.friendship_id, false)}
            >
              Decline
            </button>
          </>
        ) : (
          <span className="pending-status">Pending</span>
        )}
      </div>
    </div>
  );
};

const UserSearchCard = ({ user, onSendRequest }) => {
  const getActionButton = () => {
    switch (user.relationship_status) {
      case "friend":
        return <span className="status-badge friend">Friends</span>;
      case "incoming_request":
        return <span className="status-badge pending">Request Received</span>;
      case "outgoing_request":
        return <span className="status-badge pending">Request Sent</span>;
      default:
        return (
          <button className="add-friend-btn" onClick={onSendRequest}>
            Add Friend
          </button>
        );
    }
  };

  return (
    <div className="user-search-card">
      <div className="user-info">
        <div className="user-avatar">
          {user.first_name ? user.first_name[0] : user.username[0]}
        </div>
        <div className="user-details">
          <h4>{user.username}</h4>
          {user.full_name && user.full_name !== user.username && (
            <p>{user.full_name}</p>
          )}
        </div>
      </div>

      <div className="user-actions">{getActionButton()}</div>
    </div>
  );
};

export default FriendsManager;
