import React, { useState } from 'react';
import Head from 'next/head';
import MainForm from '../components/mainForm';
import StitchesLogo from '../components/StitchesLogo';
import { styled } from '../stitches.config';
import { Box } from '../components/box';
import { Output } from '../components/output';

const Text = styled('p', {
  fontFamily: '$system',
  color: '$hiContrast',
});

const Link = styled('a', {
  fontFamily: '$system',
  textDecoration: 'none',
  color: '$purple600',
});

const Container = styled('div', {
  marginX: 'auto',
  paddingX: '$3',

  variants: {
    size: {
      1: {
        maxWidth: '300px',
      },
      2: {
        maxWidth: '585px',
      },
      3: {
        maxWidth: '865px',
      },
    },
  },
});

export default function Home() {
  return (
    <Box css={{ paddingY: '$6' }}>
      <Head>
        <title>Main project</title>
      </Head>
      <Container size={{ '@initial': '1', '@bp1': '2' }}>
        <Text as="h1">Main project</Text>
        <MainForm />
        <Output>Hello</Output>
      </Container>
    </Box>
  );
}
