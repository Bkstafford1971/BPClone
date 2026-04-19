package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.model.Team;
import javax.swing.*;
import java.awt.*;

/**
 * Main league dashboard showing overview, standings, and navigation.
 */
public class LeagueDashboard extends JPanel {
    
    private BloodspireApp app;
    private GameStateManager gameStateManager;
    private JLabel weekLabel;
    private JLabel leagueNameLabel;
    private JTextArea standingsArea;
    
    public LeagueDashboard(BloodspireApp app, GameStateManager gameStateManager) {
        this.app = app;
        this.gameStateManager = gameStateManager;
        initializeUI();
    }
    
    private void initializeUI() {
        setLayout(new BorderLayout());
        setBackground(new Color(30, 30, 40));
        
        // Top panel with navigation
        JPanel topPanel = createNavigationPanel();
        add(topPanel, BorderLayout.NORTH);
        
        // Center panel with league info
        JPanel centerPanel = new JPanel(new GridBagLayout());
        centerPanel.setBackground(new Color(30, 30, 40));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        // League Name
        leagueNameLabel = new JLabel("League: Not Loaded");
        leagueNameLabel.setFont(new Font("Arial", Font.BOLD, 24));
        leagueNameLabel.setForeground(new Color(200, 200, 200));
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 2;
        centerPanel.add(leagueNameLabel, gbc);
        
        // Current Week
        weekLabel = new JLabel("Week: 1");
        weekLabel.setFont(new Font("Arial", Font.PLAIN, 18));
        weekLabel.setForeground(Color.LIGHT_GRAY);
        gbc.gridy = 1;
        centerPanel.add(weekLabel, gbc);
        
        // Standings
        JLabel standingsTitle = new JLabel("League Standings");
        standingsTitle.setFont(new Font("Arial", Font.BOLD, 18));
        standingsTitle.setForeground(new Color(200, 50, 50));
        gbc.gridy = 2;
        gbc.gridwidth = 1;
        centerPanel.add(standingsTitle, gbc);
        
        // Standings Text Area
        standingsArea = new JTextArea(15, 40);
        standingsArea.setEditable(false);
        standingsArea.setFont(new Font("Monospace", Font.PLAIN, 14));
        standingsArea.setBackground(new Color(20, 20, 30));
        standingsArea.setForeground(Color.WHITE);
        JScrollPane scrollPane = new JScrollPane(standingsArea);
        scrollPane.setPreferredSize(new Dimension(500, 300));
        gbc.gridx = 0;
        gbc.gridy = 3;
        gbc.gridwidth = 2;
        centerPanel.add(scrollPane, gbc);
        
        // Action Buttons
        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.setBackground(new Color(30, 30, 40));
        
        JButton advanceWeekBtn = new JButton("Advance Week");
        advanceWeekBtn.addActionListener(e -> advanceWeek());
        
        JButton executeMatchesBtn = new JButton("Execute Matches");
        executeMatchesBtn.addActionListener(e -> executeMatches());
        
        JButton refreshBtn = new JButton("Refresh");
        refreshBtn.addActionListener(e -> refresh());
        
        buttonPanel.add(advanceWeekBtn);
        buttonPanel.add(executeMatchesBtn);
        buttonPanel.add(refreshBtn);
        
        gbc.gridy = 4;
        centerPanel.add(buttonPanel, gbc);
        
        add(centerPanel, BorderLayout.CENTER);
        
        refresh();
    }
    
    private JPanel createNavigationPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        panel.setBackground(new Color(40, 40, 50));
        
        JButton teamBtn = new JButton("Team Management");
        teamBtn.addActionListener(e -> app.showScreen("TEAM"));
        
        JButton arenaBtn = new JButton("Arena");
        arenaBtn.addActionListener(e -> app.showScreen("ARENA"));
        
        panel.add(teamBtn);
        panel.add(arenaBtn);
        
        return panel;
    }
    
    /**
     * Advance to the next week
     */
    private void advanceWeek() {
        try {
            gameStateManager.advanceWeek();
            JOptionPane.showMessageDialog(this, 
                "Week advanced to " + gameStateManager.getCurrentWeek(),
                "Week Advanced", JOptionPane.INFORMATION_MESSAGE);
            refresh();
        } catch (Exception e) {
            JOptionPane.showMessageDialog(this, 
                "Error advancing week: " + e.getMessage(),
                "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    /**
     * Execute matches for current week
     */
    private void executeMatches() {
        try {
            var results = gameStateManager.executeWeekMatches();
            
            StringBuilder sb = new StringBuilder("Match Results:\n\n");
            for (var result : results) {
                sb.append(result.getWinnerTeam().getName())
                  .append(" defeated ")
                  .append(result.getLoserTeam().getName())
                  .append("\n");
            }
            
            JOptionPane.showMessageDialog(this, 
                sb.toString(),
                "Match Results", JOptionPane.INFORMATION_MESSAGE);
            refresh();
        } catch (Exception e) {
            JOptionPane.showMessageDialog(this, 
                "Error executing matches: " + e.getMessage(),
                "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    /**
     * Refresh the dashboard display
     */
    public void refresh() {
        if (gameStateManager.getLeague() != null) {
            leagueNameLabel.setText("League: " + gameStateManager.getLeague().getName());
        }
        weekLabel.setText("Week: " + gameStateManager.getCurrentWeek());
        
        // Update standings
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("%-20s %-10s %-10s %-10s%n", "Team", "Wins", "Losses", "Budget"));
        sb.append("=".repeat(60)).append("\n");
        
        for (Team team : gameStateManager.getTeams()) {
            int wins = calculateWins(team);
            int losses = calculateLosses(team);
            sb.append(String.format("%-20s %-10d %-10d $%-9d%n", 
                team.getName(), wins, losses, team.getBudget()));
        }
        
        standingsArea.setText(sb.toString());
    }
    
    private int calculateWins(Team team) {
        int wins = 0;
        for (var result : gameStateManager.getMatchHistory()) {
            if (result.getWinnerTeam() == team) {
                wins++;
            }
        }
        return wins;
    }
    
    private int calculateLosses(Team team) {
        int losses = 0;
        for (var result : gameStateManager.getMatchHistory()) {
            if (result.getLoserTeam() == team) {
                losses++;
            }
        }
        return losses;
    }
}
