package com.bloodspire.server;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.model.*;
import java.io.*;
import java.net.*;
import java.util.List;

/**
 * Socket-based server that allows the desktop client to connect and interact with the game.
 * Replaces league_server.py functionality for Java desktop application.
 */
public class LeagueServer {
    
    private int port;
    private ServerSocket serverSocket;
    private GameStateManager gameStateManager;
    private volatile boolean running;
    
    public LeagueServer(int port) {
        this.port = port;
        this.gameStateManager = new GameStateManager();
        this.running = false;
    }
    
    /**
     * Start the server
     */
    public void start() throws IOException {
        serverSocket = new ServerSocket(port);
        running = true;
        System.out.println("League Server started on port " + port);
        
        while (running) {
            try {
                Socket clientSocket = serverSocket.accept();
                handleClient(clientSocket);
            } catch (IOException e) {
                if (running) {
                    System.err.println("Error accepting client: " + e.getMessage());
                }
            }
        }
    }
    
    /**
     * Handle a client connection
     */
    private void handleClient(Socket socket) {
        Thread clientThread = new Thread(() -> {
            try (BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                 PrintWriter out = new PrintWriter(socket.getOutputStream(), true)) {
                
                String inputLine;
                while ((inputLine = in.readLine()) != null && running) {
                    String response = processCommand(inputLine);
                    out.println(response);
                    
                    if (inputLine.equals("QUIT")) {
                        break;
                    }
                }
            } catch (IOException e) {
                System.err.println("Client connection error: " + e.getMessage());
            } finally {
                try {
                    socket.close();
                } catch (IOException e) {
                    // Ignore
                }
            }
        });
        clientThread.start();
    }
    
    /**
     * Process a command from the client
     */
    private String processCommand(String command) {
        String[] parts = command.split("\\|");
        String cmdType = parts[0];
        
        switch (cmdType) {
            case "CREATE_LEAGUE":
                return createLeague(parts);
            case "GET_TEAMS":
                return getTeams();
            case "GET_FREE_AGENTS":
                return getFreeAgents();
            case "HIRE_WARRIOR":
                return hireWarrior(parts);
            case "TRAIN_WARRIOR":
                return trainWarrior(parts);
            case "ADVANCE_WEEK":
                return advanceWeek();
            case "EXECUTE_MATCHES":
                return executeMatches();
            case "GET_MATCH_HISTORY":
                return getMatchHistory();
            case "SAVE_LEAGUE":
                return saveLeague(parts);
            case "LOAD_LEAGUE":
                return loadLeague(parts);
            case "QUIT":
                stop();
                return "GOODBYE";
            default:
                return "ERROR|Unknown command: " + cmdType;
        }
    }
    
    private String createLeague(String[] parts) {
        try {
            String name = parts[1];
            int numTeams = Integer.parseInt(parts[2]);
            gameStateManager.createLeague(name, numTeams);
            return "OK|League created: " + name;
        } catch (Exception e) {
            return "ERROR|" + e.getMessage();
        }
    }
    
    private String getTeams() {
        StringBuilder sb = new StringBuilder("TEAMS|");
        for (Team team : gameStateManager.getTeams()) {
            sb.append(team.getName()).append(",").append(team.getBudget()).append(";");
        }
        return sb.toString();
    }
    
    private String getFreeAgents() {
        StringBuilder sb = new StringBuilder("FREE_AGENTS|");
        for (Warrior warrior : gameStateManager.getFreeAgents()) {
            sb.append(warrior.getFullName()).append(",").append(warrior.getRace()).append(";");
        }
        return sb.toString();
    }
    
    private String hireWarrior(String[] parts) {
        try {
            String teamName = parts[1];
            String warriorName = parts[2];
            Team team = findTeamByName(teamName);
            Warrior warrior = findFreeAgentByName(warriorName);
            
            if (team != null && warrior != null) {
                boolean success = gameStateManager.hireFreeAgent(team, warrior);
                return success ? "OK|Warrior hired" : "ERROR|Failed to hire warrior";
            }
            return "ERROR|Team or warrior not found";
        } catch (Exception e) {
            return "ERROR|" + e.getMessage();
        }
    }
    
    private String trainWarrior(String[] parts) {
        try {
            String warriorName = parts[1];
            Stat stat = Stat.valueOf(parts[2]);
            Warrior warrior = findWarriorByName(warriorName);
            
            if (warrior != null) {
                gameStateManager.trainWarrior(warrior, stat);
                return "OK|Warrior trained in " + stat;
            }
            return "ERROR|Warrior not found";
        } catch (Exception e) {
            return "ERROR|" + e.getMessage();
        }
    }
    
    private String advanceWeek() {
        gameStateManager.advanceWeek();
        return "OK|Week advanced to " + gameStateManager.getCurrentWeek();
    }
    
    private String executeMatches() {
        List<GameStateManager.MatchResult> results = gameStateManager.executeWeekMatches();
        StringBuilder sb = new StringBuilder("MATCH_RESULTS|");
        for (GameStateManager.MatchResult result : results) {
            Team winner = result.getWinnerTeam();
            Team loser = result.getLoserTeam();
            sb.append(winner.getName()).append(" defeated ").append(loser.getName()).append(";");
        }
        return sb.toString();
    }
    
    private String getMatchHistory() {
        StringBuilder sb = new StringBuilder("MATCH_HISTORY|");
        for (GameStateManager.MatchResult result : gameStateManager.getMatchHistory()) {
            sb.append(result.getWinnerTeam().getName()).append(" beat ").append(result.getLoserTeam().getName()).append(";");
        }
        return sb.toString();
    }
    
    private String saveLeague(String[] parts) {
        try {
            String filePath = parts[1];
            gameStateManager.saveLeague(filePath);
            return "OK|League saved to " + filePath;
        } catch (Exception e) {
            return "ERROR|" + e.getMessage();
        }
    }
    
    private String loadLeague(String[] parts) {
        try {
            String filePath = parts[1];
            boolean success = gameStateManager.loadLeague(filePath);
            return success ? "OK|League loaded" : "ERROR|Failed to load league";
        } catch (Exception e) {
            return "ERROR|" + e.getMessage();
        }
    }
    
    private Team findTeamByName(String name) {
        for (Team team : gameStateManager.getTeams()) {
            if (team.getName().equals(name)) {
                return team;
            }
        }
        return null;
    }
    
    private Warrior findFreeAgentByName(String name) {
        for (Warrior warrior : gameStateManager.getFreeAgents()) {
            if (warrior.getFullName().equals(name)) {
                return warrior;
            }
        }
        return null;
    }
    
    private Warrior findWarriorByName(String name) {
        for (Team team : gameStateManager.getTeams()) {
            for (Warrior warrior : team.getWarriors()) {
                if (warrior.getFullName().equals(name)) {
                    return warrior;
                }
            }
        }
        for (Warrior warrior : gameStateManager.getFreeAgents()) {
            if (warrior.getFullName().equals(name)) {
                return warrior;
            }
        }
        return null;
    }
    
    /**
     * Stop the server
     */
    public void stop() {
        running = false;
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (IOException e) {
            System.err.println("Error closing server socket: " + e.getMessage());
        }
    }
    
    /**
     * Get the game state manager
     */
    public GameStateManager getGameStateManager() {
        return gameStateManager;
    }
    
    /**
     * Main method to run the server standalone
     */
    public static void main(String[] args) {
        int port = 8765; // Default port
        
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.out.println("Invalid port number, using default: " + port);
            }
        }
        
        LeagueServer server = new LeagueServer(port);
        try {
            server.start();
        } catch (IOException e) {
            System.err.println("Failed to start server: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
