package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.engine.CombatEngine;
import com.bloodspire.engine.NarrativeEngine;
import com.bloodspire.model.*;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Arena screen for viewing and simulating fights.
 */
public class ArenaScreen extends JPanel {
    
    private BloodspireApp app;
    private GameStateManager gameStateManager;
    private CombatEngine combatEngine;
    private NarrativeEngine narrativeEngine;
    
    private JComboBox<String> fighter1Combo;
    private JComboBox<String> fighter2Combo;
    private JComboBox<String> team1Combo;
    private JComboBox<String> team2Combo;
    private JTextArea combatLog;
    private JLabel fighter1HealthLabel;
    private JLabel fighter2HealthLabel;
    private JProgressBar fighter1HealthBar;
    private JProgressBar fighter2HealthBar;
    private JProgressBar fighter1StaminaBar;
    private JProgressBar fighter2StaminaBar;
    
    private Warrior currentFighter1;
    private Warrior currentFighter2;
    private boolean fightInProgress;
    
    public ArenaScreen(BloodspireApp app, GameStateManager gameStateManager) {
        this.app = app;
        this.gameStateManager = gameStateManager;
        this.combatEngine = new CombatEngine();
        this.narrativeEngine = new NarrativeEngine();
        this.fightInProgress = false;
        initializeUI();
    }
    
    private void initializeUI() {
        setLayout(new BorderLayout());
        setBackground(new Color(30, 30, 40));
        
        // Top panel with fighter selection
        JPanel topPanel = createSelectionPanel();
        add(topPanel, BorderLayout.NORTH);
        
        // Center - Combat display
        JPanel centerPanel = createCombatDisplay();
        add(centerPanel, BorderLayout.CENTER);
        
        // Bottom - Action buttons
        JPanel bottomPanel = createActionPanel();
        add(bottomPanel, BorderLayout.SOUTH);
        
        refresh();
    }
    
    private JPanel createSelectionPanel() {
        JPanel panel = new JPanel(new GridLayout(2, 4, 10, 10));
        panel.setBackground(new Color(40, 40, 50));
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Team 1 selection
        panel.add(new JLabel("Team 1:"));
        team1Combo = new JComboBox<>();
        team1Combo.addActionListener(e -> updateFighter1Combo());
        panel.add(team1Combo);
        
        // Fighter 1 selection
        panel.add(new JLabel("Fighter 1:"));
        fighter1Combo = new JComboBox<>();
        panel.add(fighter1Combo);
        
        // Team 2 selection
        panel.add(new JLabel("Team 2:"));
        team2Combo = new JComboBox<>();
        team2Combo.addActionListener(e -> updateFighter2Combo());
        panel.add(team2Combo);
        
        // Fighter 2 selection
        panel.add(new JLabel("Fighter 2:"));
        fighter2Combo = new JComboBox<>();
        panel.add(fighter2Combo);
        
        return panel;
    }
    
    private JPanel createCombatDisplay() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        // Fighter 1 info (left side)
        gbc.gridx = 0;
        gbc.gridy = 0;
        gbc.gridwidth = 1;
        JPanel fighter1Panel = createFighterStatusPanel(true);
        panel.add(fighter1Panel, gbc);
        
        // Fighter 2 info (right side)
        gbc.gridx = 2;
        JPanel fighter2Panel = createFighterStatusPanel(false);
        panel.add(fighter2Panel, gbc);
        
        // Combat log (center bottom)
        gbc.gridx = 0;
        gbc.gridy = 1;
        gbc.gridwidth = 3;
        gbc.weighty = 1.0;
        gbc.fill = GridBagConstraints.BOTH;
        
        combatLog = new JTextArea(20, 60);
        combatLog.setEditable(false);
        combatLog.setFont(new Font("Monospace", Font.PLAIN, 12));
        combatLog.setBackground(new Color(10, 10, 20));
        combatLog.setForeground(Color.WHITE);
        JScrollPane logScroll = new JScrollPane(combatLog);
        panel.add(logScroll, gbc);
        
        return panel;
    }
    
    private JPanel createFighterStatusPanel(boolean isFighter1) {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(30, 30, 40));
        panel.setBorder(BorderFactory.createLineBorder(Color.GRAY, 2));
        panel.setPreferredSize(new Dimension(300, 150));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridx = 0;
        gbc.gridy = 0;
        
        // Name label
        JLabel nameLabel = new JLabel(isFighter1 ? "Fighter 1" : "Fighter 2");
        nameLabel.setFont(new Font("Arial", Font.BOLD, 16));
        nameLabel.setForeground(Color.WHITE);
        panel.add(nameLabel, gbc);
        
        // Health bar
        gbc.gridy++;
        JLabel healthLabel = new JLabel("Health:");
        healthLabel.setForeground(Color.LIGHT_GRAY);
        panel.add(healthLabel, gbc);
        
        gbc.gridx++;
        JProgressBar healthBar = new JProgressBar(0, 100);
        healthBar.setValue(100);
        healthBar.setStringPainted(true);
        healthBar.setForeground(Color.RED);
        if (isFighter1) {
            fighter1HealthBar = healthBar;
            fighter1HealthLabel = nameLabel;
        } else {
            fighter2HealthBar = healthBar;
            fighter2HealthLabel = nameLabel;
        }
        panel.add(healthBar, gbc);
        
        // Stamina bar
        gbc.gridx = 0;
        gbc.gridy++;
        JLabel staminaLabel = new JLabel("Stamina:");
        staminaLabel.setForeground(Color.LIGHT_GRAY);
        panel.add(staminaLabel, gbc);
        
        gbc.gridx++;
        JProgressBar staminaBar = new JProgressBar(0, 100);
        staminaBar.setValue(100);
        staminaBar.setStringPainted(true);
        staminaBar.setForeground(Color.BLUE);
        if (isFighter1) {
            fighter1StaminaBar = staminaBar;
        } else {
            fighter2StaminaBar = staminaBar;
        }
        panel.add(staminaBar, gbc);
        
        return panel;
    }
    
    private JPanel createActionPanel() {
        JPanel panel = new JPanel(new FlowLayout());
        panel.setBackground(new Color(40, 40, 50));
        
        JButton simulateBtn = new JButton("Simulate Fight");
        simulateBtn.setFont(new Font("Arial", Font.BOLD, 14));
        simulateBtn.addActionListener(e -> simulateFight());
        
        JButton stepBtn = new JButton("Step Through");
        stepBtn.addActionListener(e -> stepThroughFight());
        
        JButton clearBtn = new JButton("Clear Log");
        clearBtn.addActionListener(e -> combatLog.setText(""));
        
        JButton backBtn = new JButton("Back to Dashboard");
        backBtn.addActionListener(e -> app.showScreen("DASHBOARD"));
        
        panel.add(simulateBtn);
        panel.add(stepBtn);
        panel.add(clearBtn);
        panel.add(backBtn);
        
        return panel;
    }
    
    /**
     * Refresh the screen
     */
    public void refresh() {
        // Update team combos
        team1Combo.removeAllItems();
        team2Combo.removeAllItems();
        
        for (Team team : gameStateManager.getTeams()) {
            team1Combo.addItem(team.getName());
            team2Combo.addItem(team.getName());
        }
        
        if (team1Combo.getItemCount() > 0) team1Combo.setSelectedIndex(0);
        if (team2Combo.getItemCount() > 1) team2Combo.setSelectedIndex(1);
        
        updateFighter1Combo();
        updateFighter2Combo();
        
        combatLog.setText("");
        resetHealthBars();
    }
    
    private void updateFighter1Combo() {
        fighter1Combo.removeAllItems();
        String teamName = (String) team1Combo.getSelectedItem();
        Team team = findTeamByName(teamName);
        
        if (team != null) {
            for (Warrior warrior : team.getWarriors()) {
                fighter1Combo.addItem(warrior.getFullName());
            }
        }
    }
    
    private void updateFighter2Combo() {
        fighter2Combo.removeAllItems();
        String teamName = (String) team2Combo.getSelectedItem();
        Team team = findTeamByName(teamName);
        
        if (team != null) {
            for (Warrior warrior : team.getWarriors()) {
                fighter2Combo.addItem(warrior.getFullName());
            }
        }
    }
    
    private void resetHealthBars() {
        if (fighter1HealthBar != null) {
            fighter1HealthBar.setValue(100);
            fighter1StaminaBar.setValue(100);
        }
        if (fighter2HealthBar != null) {
            fighter2HealthBar.setValue(100);
            fighter2StaminaBar.setValue(100);
        }
    }
    
    private void simulateFight() {
        if (fightInProgress) {
            JOptionPane.showMessageDialog(this, 
                "A fight is already in progress!",
                "Fight In Progress", JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        String f1Name = (String) fighter1Combo.getSelectedItem();
        String f2Name = (String) fighter2Combo.getSelectedItem();
        
        if (f1Name == null || f2Name == null || f1Name.equals(f2Name)) {
            JOptionPane.showMessageDialog(this, 
                "Please select two different fighters",
                "Invalid Selection", JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        Warrior warrior1 = findWarriorByName(f1Name, (String) team1Combo.getSelectedItem());
        Warrior warrior2 = findWarriorByName(f2Name, (String) team2Combo.getSelectedItem());
        
        if (warrior1 == null || warrior2 == null) {
            JOptionPane.showMessageDialog(this, 
                "Could not find selected fighters",
                "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        // Clone warriors for simulation
        currentFighter1 = warrior1.clone();
        currentFighter2 = warrior2.clone();
        
        // Reset UI
        combatLog.setText("");
        resetHealthBars();
        fightInProgress = true;
        
        // Run simulation in background thread
        SwingWorker<CombatResult, String> worker = new SwingWorker<>() {
            @Override
            protected CombatResult doInBackground() {
                List<String> events = new ArrayList<>();
                
                // Add match start narrative
                publish(narrativeEngine.generateMatchStart(currentFighter1, currentFighter2, "The Arena"));
                
                int round = 1;
                CombatResult result = null;
                
                while (result == null && round <= 20) {
                    publish("\n--- Round " + round + " ---");
                    publish("HP: " + currentFighter1.getCurrentHealth() + "/" + currentFighter1.getMaxHealth() + 
                           " | Stamina: " + currentFighter1.getCurrentStamina());
                    publish("HP: " + currentFighter2.getCurrentHealth() + "/" + currentFighter2.getMaxHealth() + 
                           " | Stamina: " + currentFighter2.getCurrentStamina());
                    
                    // Simulate one round
                    result = combatEngine.simulateRound(currentFighter1, currentFighter2, round);
                    
                    // Generate narrative for actions
                    if (result.getLastActionNarrative() != null) {
                        publish(result.getLastActionNarrative());
                    }
                    
                    round++;
                    
                    try {
                        Thread.sleep(500); // Pause for dramatic effect
                    } catch (InterruptedException e) {
                        break;
                    }
                }
                
                return result;
            }
            
            @Override
            protected void process(List<String> chunks) {
                for (String text : chunks) {
                    combatLog.append(text + "\n");
                    combatLog.setCaretPosition(combatLog.getDocument().getLength());
                }
            }
            
            @Override
            protected void done() {
                try {
                    CombatResult result = get();
                    if (result != null) {
                        Warrior winner = result.getWinner();
                        String method = result.getEndMethod();
                        
                        combatLog.append("\n\n=== FIGHT OVER ===\n");
                        combatLog.append(narrativeEngine.generateMatchEnd(winner, 
                            winner == currentFighter1 ? currentFighter2 : currentFighter1, method));
                        combatLog.append("\nWinner: " + winner.getFullName() + " by " + method);
                        
                        // Update health bars to final state
                        fighter1HealthBar.setValue((int)(currentFighter1.getHealthPercent() * 100));
                        fighter2HealthBar.setValue((int)(currentFighter2.getHealthPercent() * 100));
                        fighter1StaminaBar.setValue((int)(currentFighter1.getStaminaPercent() * 100));
                        fighter2StaminaBar.setValue((int)(currentFighter2.getStaminaPercent() * 100));
                    }
                } catch (Exception e) {
                    combatLog.append("\nError during fight: " + e.getMessage());
                } finally {
                    fightInProgress = false;
                }
            }
        };
        
        worker.execute();
    }
    
    private void stepThroughFight() {
        JOptionPane.showMessageDialog(this, 
            "Step-through mode coming soon!\nUse 'Simulate Fight' for full auto-simulation.",
            "Not Implemented", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private Team findTeamByName(String name) {
        for (Team team : gameStateManager.getTeams()) {
            if (team.getName().equals(name)) {
                return team;
            }
        }
        return null;
    }
    
    private Warrior findWarriorByName(String name, String teamName) {
        Team team = findTeamByName(teamName);
        if (team != null) {
            for (Warrior warrior : team.getWarriors()) {
                if (warrior.getFullName().equals(name)) {
                    return warrior;
                }
            }
        }
        return null;
    }
}
