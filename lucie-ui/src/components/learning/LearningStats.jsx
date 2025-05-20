import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  LinearProgress,
  Card,
  CardContent,
  Tooltip,
} from '@mui/material';
import { useTheme } from '../../hooks/useTheme';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/lab';
import { motion } from 'framer-motion';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import PsychologyIcon from '@mui/icons-material/Psychology';
import SpeedIcon from '@mui/icons-material/Speed';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';

const LearningStats = ({ stats }) => {
  const { theme } = useTheme();

  const StatCard = ({ title, value, icon, color, tooltip }) => (
    <Card
      sx={{
        height: '100%',
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Box
            sx={{
              backgroundColor: `${color}20`,
              borderRadius: '50%',
              p: 1,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6">{title}</Typography>
        </Box>
        <Tooltip title={tooltip}>
          <Typography variant="h4" color={color}>
            {value}
          </Typography>
        </Tooltip>
      </CardContent>
    </Card>
  );

  const ProgressSection = ({ title, progress, color }) => (
    <Box mb={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="subtitle1">{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {progress}%
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 8,
          borderRadius: 4,
          backgroundColor: `${color}20`,
          '& .MuiLinearProgress-bar': {
            backgroundColor: color,
          },
        }}
      />
    </Box>
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 3,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Typography variant="h6" gutterBottom>
          Learning Statistics
        </Typography>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Accuracy"
              value={`${stats.accuracy}%`}
              icon={<TrendingUpIcon sx={{ color: theme.palette.success.main }} />}
              color={theme.palette.success.main}
              tooltip="Overall response accuracy"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Learning Rate"
              value={`${stats.learningRate}%`}
              icon={<SpeedIcon sx={{ color: theme.palette.info.main }} />}
              color={theme.palette.info.main}
              tooltip="Rate of knowledge acquisition"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Concepts"
              value={stats.concepts}
              icon={<PsychologyIcon sx={{ color: theme.palette.warning.main }} />}
              color={theme.palette.warning.main}
              tooltip="Total concepts learned"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Achievements"
              value={stats.achievements}
              icon={<EmojiEventsIcon sx={{ color: theme.palette.secondary.main }} />}
              color={theme.palette.secondary.main}
              tooltip="Learning milestones achieved"
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                backgroundColor: theme.palette.background.default,
                height: '100%',
              }}
            >
              <Typography variant="subtitle1" gutterBottom>
                Learning Progress
              </Typography>
              <ProgressSection
                title="Knowledge Base"
                progress={stats.knowledgeProgress}
                color={theme.palette.primary.main}
              />
              <ProgressSection
                title="Response Quality"
                progress={stats.responseProgress}
                color={theme.palette.success.main}
              />
              <ProgressSection
                title="User Satisfaction"
                progress={stats.satisfactionProgress}
                color={theme.palette.warning.main}
              />
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                backgroundColor: theme.palette.background.default,
                height: '100%',
              }}
            >
              <Typography variant="subtitle1" gutterBottom>
                Recent Achievements
              </Typography>
              <Timeline>
                {stats.recentAchievements.map((achievement, index) => (
                  <TimelineItem key={index}>
                    <TimelineSeparator>
                      <TimelineDot color="primary" />
                      {index < stats.recentAchievements.length - 1 && <TimelineConnector />}
                    </TimelineSeparator>
                    <TimelineContent>
                      <Typography variant="subtitle2">{achievement.title}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {achievement.date}
                      </Typography>
                    </TimelineContent>
                  </TimelineItem>
                ))}
              </Timeline>
            </Paper>
          </Grid>
        </Grid>
      </Paper>
    </motion.div>
  );
};

export default LearningStats;
