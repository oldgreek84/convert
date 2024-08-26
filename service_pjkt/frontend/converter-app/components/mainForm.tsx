import React, { useState } from 'react';
import * as Form from '@radix-ui/react-form';
import { styled } from '@stitches/react';

type Props = {
  isProcessing: boolean,
  onSubmit: (fileData: string) => void,
}

// const [name, setName] = useState('');
// const [selectedFile, setSelectedFile] = useState(null);

export const MainForm:React.FC<Props> = ({ onSubmit, isProcessing }) => {
  const [file, setFile] = useState<File | null>(null);
  const hadleSubmit: React.FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    console.log('----- SUB');
    const fileInput = event.target;
    const file = fileInput.files[0];
    setFile(file);
    onSubmit(file);
  };

  const onFileUploadChange = (e: ChangeEvent<HTMLInputElement>) => {
    console.log('----- UP');
  };
  return (

    <FormRoot>
      <FormField name="files">
        <Flex css={{ alignItems: 'baseline', justifyContent: 'space-between' }}>
          <FormLabel>Files</FormLabel>
          <FormMessage match="valueMissing">Choose a file to convert</FormMessage>
        </Flex>
        <Form.Control asChild>
          <Input type="file" required onSubmit={onFileUploadChange}></Input>
        </Form.Control>

      </FormField>
      <FormField name="some">
        <Flex css={{ alignItems: 'baseline', justifyContent: 'space-between' }}>
          <FormLabel>File type</FormLabel>
          <FormMessage match="valueMissing">Enter type</FormMessage>
        </Flex>

        <Form.Control asChild>
          <select> <option>1</option><option>2</option></select>
        </Form.Control>

      </FormField>
      <Form.Submit asChild disabled={isProcessing}>
        <Button css={{ marginTop: 10 }}>{isProcessing ? 'Processing...': 'Send'}</Button>
      </Form.Submit>
    </FormRoot>
  );
};

const FormRoot = styled(Form.Root, {
  width: 260,
});
//
const FormField = styled(Form.Field, {
  display: 'grid',
  marginBottom: 10,
});

const FormLabel = styled(Form.Label, {
  fontSize: 15,
  fontWeight: 500,
  lineHeight: '35px',
  color: '$foreground',
});

const FormMessage = styled(Form.Message, {
  fontSize: 13,
  color: 'red',
  opacity: 0.8,
});

const Flex = styled('div', { display: 'flex' });

const inputStyles = {
  'all': 'unset',
  'boxSizing': 'border-box',
  'width': '100%',
  'display': 'inline-flex',
  'alignItems': 'center',
  'justifyContent': 'center',
  'borderRadius': 4,

  'fontSize': 15,
  'color': '$foreground',
  'backgroundColor': '$gray300',
  'boxShadow': `0 0 0 1px $gray400`,
  '&:hover': { boxShadow: `0 0 0 1px $gray600` },
  '&:focus': { boxShadow: `0 0 0 2px $purple600` },
  '&::selection': { backgroundColor: '$gray600', color: '$foreground' },
};

const Input = styled('input', {
  ...inputStyles,
  height: 35,
  lineHeight: 1,
  padding: '0 10px',
});

const Button = styled('button', {
  'all': 'unset',
  'boxSizing': 'border-box',
  'display': 'inline-flex',
  'alignItems': 'center',
  'justifyContent': 'center',
  'borderRadius': 4,
  'padding': '0 15px',
  'fontSize': 15,
  'lineHeight': 1,
  'fontWeight': 500,
  'height': 35,
  'width': '100%',

  'backgroundColor': '$purple500',
  'color': 'white',
  'boxShadow': `0 2px 10px $gray400`,
  '&:not(:disabled):hover': { backgroundColor: '$purple600' },
  '&:not(:disabled):focus': { boxShadow: `0 0 0 2px black` },
});

export default MainForm;
