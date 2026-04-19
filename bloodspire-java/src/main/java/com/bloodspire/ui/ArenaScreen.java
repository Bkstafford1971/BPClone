package com.bloodspire.ui;

import com.bloodspire.manager.GameStateManager;
import com.bloodspire.engine.CombatEngine;
import com.bloodspire.model.Warrior;
import javax.swing.*;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Arena Screen for viewing and simulating fights
 */
public class ArenaScreen extends JPanel {
    
    private JFrame parentFrame;
    private GameStateManager gameStateManager;
    private JTextArea combatLog;
    private JButton startFightButton;
    private JButton autoSimulateButton;
    private boolean isFighting = false;
    private CombatEngine combatEngine;
    
    public ArenaScreen(JFrame frame, GameStateManager manager) {
        this.parentFrame = frame;
        this.gameStateManager = manager;
        this.combatEngine = new CombatEngine();
        
        setLayout(new BorderLayout());
        setBackground(new Color(20, 20, 30));
        
        // Header
        JPanel headerPanel = createHeaderPanel();
        add(headerPanel, BorderLayout.NORTH);
        
        // Main arena view
        JPanel arenaPanel = createArenaPanel();
        add(arenaPanel, BorderLayout.CENTER);
        
        // Controls
        JPanel controlPanel = createControlPanel();
        add(controlPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createHeaderPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 60));
        
        JLabel titleLabel = new JLabel("The Arena");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 20));
        titleLabel.setForeground(new Color(200, 50, 50));
        panel.add(titleLabel);
        
        return panel;
    }
    
    private JPanel createArenaPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBackground(new Color(20, 20, 30));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        
        // Fighter 1 (Left)
        gbc.gridx = 0;
        gbc.gridy = 0;
        panel.add(createFighterDisplay("Fighter 1", true), gbc);
        
        // VS label
        gbc.gridx = 1;
        JLabel vsLabel = new JLabel("VS");
        vsLabel.setFont(new Font("Arial", Font.BOLD, 48));
        vsLabel.setForeground(new Color(200, 50, 50));
        panel.add(vsLabel, gbc);
        
        // Fighter 2 (Right)
        gbc.gridx = 2;
        panel.add(createFighterDisplay("Fighter 2", false), gbc);
        
        // Combat Log
        gbc.gridx = 0;
        gbc.gridy = 1;
        gbc.gridwidth = 3;
        gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 1.0;
        gbc.weighty = 1.0;
        panel.add(createCombatLog(), gbc);
        
        return panel;
    }
    
    private JPanel createFighterDisplay(String name, boolean isPlayer) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(300, 400));
        panel.setBorder(BorderFactory.createLineBorder(
            isPlayer ? new Color(50, 150, 50) : new Color(150, 50, 50), 2
        ));
        
        // Name
        JLabel nameLabel = new JLabel(name);
        nameLabel.setFont(new Font("Arial", Font.BOLD, 18));
        nameLabel.setForeground(Color.WHITE);
        nameLabel.setHorizontalAlignment(SwingConstants.CENTER);
        panel.add(nameLabel, BorderLayout.NORTH);
        
        // Stats panel
        JPanel statsPanel = new JPanel(new GridBagLayout());
        statsPanel.setBackground(new Color(30, 30, 40));
        
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 10, 5, 10);
        gbc.anchor = GridBagConstraints.WEST;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        
        // Health bar
        gbc.gridx = 0;
        gbc.gridy = 0;
        statsPanel.add(createStatLabel("Health:"), gbc);
        gbc.gridx = 1;
        JProgressBar healthBar = createProgressBar(100, 100, new Color(50, 200, 50));
        statsPanel.add(healthBar, gbc);
        
        // Stamina bar
        gbc.gridx = 0;
        gbc.gridy = 1;
        statsPanel.add(createStatLabel("Stamina:"), gbc);
        gbc.gridx = 1;
        JProgressBar staminaBar = createProgressBar(100, 100, new Color(50, 50, 200));
        statsPanel.add(staminaBar, gbc);
        
        // Wounds
        gbc.gridx = 0;
        gbc.gridy = 2;
        gbc.gridwidth = 2;
        JLabel woundsLabel = new JLabel("Wounds: None");
        woundsLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        woundsLabel.setForeground(Color.WHITE);
        statsPanel.add(woundsLabel, gbc);
        
        panel.add(statsPanel, BorderLayout.CENTER);
        
        // Fighter info
        JPanel infoPanel = new JPanel(new FlowLayout(FlowLayout.CENTER));
        infoPanel.setBackground(new Color(30, 30, 40));
        JLabel infoLabel = new JLabel("Select fighters to begin");
        infoLabel.setFont(new Font("Arial", Font.PLAIN, 12));
        infoLabel.setForeground(Color.GRAY);
        infoPanel.add(infoLabel);
        panel.add(infoPanel, BorderLayout.SOUTH);
        
        return panel;
    }
    
    private JLabel createStatLabel(String text) {
        JLabel label = new JLabel(text);
        label.setFont(new Font("Arial", Font.BOLD, 12));
        label.setForeground(new Color(200, 200, 200));
        return label;
    }
    
    private JProgressBar createProgressBar(int max, int value, Color color) {
        JProgressBar bar = new JProgressBar(0, max);
        bar.setValue(value);
        bar.setStringPainted(true);
        bar.setForeground(color);
        bar.setBackground(new Color(60, 60, 70));
        bar.setPreferredSize(new Dimension(150, 20));
        return bar;
    }
    
    private JScrollPane createCombatLog() {
        combatLog = new JTextArea(15, 60);
        combatLog.setFont(new Font("Courier New", Font.PLAIN, 12));
        combatLog.setBackground(new Color(10, 10, 20));
        combatLog.setForeground(new Color(200, 200, 200));
        combatLog.setEditable(false);
        combatLog.setLineWrap(true);
        combatLog.setWrapStyleWord(true);
        combatLog.setText("--- Combat Log ---\nReady to fight!\n");
        
        JScrollPane scrollPane = new JScrollPane(combatLog);
        scrollPane.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(100, 100, 100)),
            "Combat Log",
            0,
            0,
            new Font("Arial", Font.BOLD, 14),
            Color.WHITE
        ));
        scrollPane.setPreferredSize(new Dimension(700, 250));
        
        return scrollPane;
    }
    
    private JPanel createControlPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 20, 15));
        panel.setBackground(new Color(40, 40, 50));
        panel.setPreferredSize(new Dimension(panel.getPreferredSize().width, 100));
        
        // Select Fighters Button
        JButton selectButton = new JButton("Select Fighters");
        selectButton.setFont(new Font("Arial", Font.BOLD, 14));
        selectButton.setPreferredSize(new Dimension(180, 50));
        selectButton.addActionListener(e -> selectFighters());
        panel.add(selectButton);
        
        // Start Fight Button
        startFightButton = new JButton("Start Fight (Step-by-Step)");
        startFightButton.setFont(new Font("Arial", Font.BOLD, 14));
        startFightButton.setPreferredSize(new Dimension(220, 50));
        startFightButton.setEnabled(false);
        startFightButton.addActionListener(e -> startFight());
        panel.add(startFightButton);
        
        // Auto Simulate Button
        autoSimulateButton = new JButton("Auto Simulate Fight");
        autoSimulateButton.setFont(new Font("Arial", Font.BOLD, 14));
        autoSimulateButton.setPreferredSize(new Dimension(200, 50));
        autoSimulateButton.setEnabled(false);
        autoSimulateButton.addActionListener(e -> autoSimulate());
        panel.add(autoSimulateButton);
        
        // Back Button
        JButton backButton = new JButton("Back to Dashboard");
        backButton.setFont(new Font("Arial", Font.BOLD, 14));
        backButton.setPreferredSize(new Dimension(180, 50));
        backButton.addActionListener(e -> goBack());
        panel.add(backButton);
        
        return panel;
    }
    
    private void selectFighters() {
        // Simple dialog for now - in full implementation would show fighter selection
        String[] options = {"Quick Match", "Choose Specific Fighters"};
        int choice = JOptionPane.showOptionDialog(
            this,
            "How would you like to select fighters?",
            "Select Fighters",
            JOptionPane.DEFAULT_OPTION,
            JOptionPane.QUESTION_MESSAGE,
            null,
            options,
            options[0]
        );
        
        if (choice == 0) {
            // Quick match - use random fighters
            appendToLog("Setting up quick match...\n");
            appendToLog("Fighter 1: Grom (Orc Brawler)\n");
            appendToLog("Fighter 2: Swift (Elf Duelist)\n");
            appendToLog("\nFighters ready! Click 'Start Fight' or 'Auto Simulate'\n");
            
            startFightButton.setEnabled(true);
            autoSimulateButton.setEnabled(true);
        } else {
            JOptionPane.showMessageDialog(
                this,
                "Fighter selection coming soon!",
                "Select Fighters",
                JOptionPane.INFORMATION_MESSAGE
            );
        }
    }
    
    private void startFight() {
        if (isFighting) {
            appendToLog("Fight already in progress...\n");
            return;
        }
        
        isFighting = true;
        appendToLog("\n=== FIGHT BEGIN ===\n");
        
        // In full implementation, this would step through combat engine
        SwingWorker<Void, String> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() {
                simulateFightSteps();
                return null;
            }
            
            @Override
            protected void done() {
                isFighting = false;
                appendToLog("\n=== FIGHT END ===\n");
            }
        };
        
        worker.execute();
    }
    
    private void autoSimulate() {
        if (isFighting) {
            appendToLog("Fight already in progress...\n");
            return;
        }
        
        isFighting = true;
        appendToLog("\n=== AUTO SIMULATION START ===\n");
        
        SwingWorker<Void, String> worker = new SwingWorker<>() {
            @Override
            protected Void doInBackground() {
                simulateFullFight();
                return null;
            }
            
            @Override
            protected void done() {
                isFighting = false;
                appendToLog("\n=== AUTO SIMULATION END ===\n");
            }
        };
        
        worker.execute();
    }
    
    private void simulateFightSteps() {
        // Placeholder for step-by-step combat simulation
        try {
            publish("Round 1: Fighters approach each other...\n");
            Thread.sleep(1000);
            publish("Round 1: Grom attacks with his axe!\n");
            Thread.sleep(1000);
            publish("Round 1: Swift dodges the attack!\n");
            Thread.sleep(1000);
            publish("Round 2: Swift counters with a swift strike!\n");
            Thread.sleep(1000);
            publish("Round 2: The blow lands! Damage dealt.\n");
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    private void simulateFullFight() {
        // Placeholder for full auto-simulation
        try {
            List<String> logLines = new ArrayList<>();
            logLines.add("Fight begins between Grom and Swift!");
            logLines.add("Round 1: Both fighters exchange blows.");
            logLines.add("Round 2: Grom lands a heavy hit!");
            logLines.add("Round 3: Swift's stamina is fading.");
            logLines.add("Round 4: Grom presses the advantage.");
            logLines.add("Round 5: Swift falls! Grom is victorious!");
            
            for (String line : logLines) {
                publish(line + "\n");
                Thread.sleep(500);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    @Override
    protected void process(List<String> chunks) {
        for (String chunk : chunks) {
            appendToLog(chunk);
        }
    }
    
    private void appendToLog(String text) {
        SwingUtilities.invokeLater(() -> {
            combatLog.append(text);
            combatLog.setCaretPosition(combatLog.getDocument().getLength());
        });
    }
    
    private void goBack() {
        LeagueDashboard dashboard = new LeagueDashboard(parentFrame, "League", false);
        parentFrame.getContentPane().removeAll();
        parentFrame.getContentPane().add(dashboard);
        parentFrame.revalidate();
        parentFrame.repaint();
    }
}
